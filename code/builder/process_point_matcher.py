"""
Class for Matching start and endpoints of a simulation

Pseudo code:
Get random start point
    if point is part of commuter within an area
        get area of startpoint
Build dount around the point (bigger buffer, substract smaller buffer
Select all points within this donut
Randomly choose one of the points
Calculate route
If does route match the wanted conditions?
    Save points to database routing table
Else choose another point
"""
import logging
from multiprocessing import Process, Queue
from threading import Thread

from helper import database
from builder import MatchingType
from helper.commuter_distribution import MatchingDistribution


class PointMatchCommand(object):
    __slots__ = ['_point_id', '_rs', '_matching_type']

    def __init__(self, point_id, rs, matching_type):
        self._point_id = point_id
        self._rs = rs
        self._matching_type = matching_type

    @property
    def point_id(self):
        return self._point_id

    @property
    def rs(self):
        return self._rs

    @property
    def matching_type(self):
        return self._matching_type


class PointMatcherProcess(Process):
    """
    Point Matcher class
    """

    def __init__(self, district_queue: Queue):
        Process.__init__(self)
        self.logging = logging.getLogger(self.__name__)
        self.dq = district_queue
        self.point_q = Queue()
        self.matcher_threads = 3

    def run(self):
        while not self.dq.empty():
            current_rs = self.dq.get()
            distribution_rs = MatchingDistribution(current_rs)
            self.logging.info('Start matching for %s', current_rs)
            self.fill_point_queue(current_rs)

            threads = []
            for i in range(self.matcher_threads):
                name = 'Matcher Thread %s' % i
                t = PointMatcherThread(self.point_q, distribution_rs)
                t.setName(name)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
            self.logging.info('Finished matching for %s', current_rs)

    def fill_point_queue(self, rs):
        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM de_sim_points_within_start WHERE parent_geometry = %s', (rs, ))
            conn.commit()
            [self.point_q.put(PointMatchCommand(p[0], rs, MatchingType.within)) for p in cur.fetchall()]
            cur.execute('SELECT id FROM de_sim_points_start WHERE parent_geometry = %s', (rs, ))
            conn.commit()
            [self.point_q.put(PointMatchCommand(p[0], rs, MatchingType.outgoing)) for p in cur.fetchall()]


class PointMatcherThread(Thread):
    def __init__(self, q: Queue, distribution: MatchingDistribution):
        """

        :param q: Queue with PointMatchCommand
        :return:
        """
        Thread.__init__(self)
        self.q = q
        self.distribution = distribution
        self.logging = logging.getLogger(self.__name__)
        self.max_retries = 5

    def run(self):
        sql_search = 'WITH s AS (SELECT * FROM de_sim_points_{tbl_s!s} WHERE id = %(start)s) ' \
                     'SELECT s.id AS start, e.id AS destination ' \
                     'FROM de_sim_points_{tbl_e!s} AS e, s ' \
                     'WHERE ST_DWithin(s.geom::geography, e.geom::geography, %(max_d)s) ' \
                     '  AND NOT ST_DWithin(s.geom::geography, e.geom::geography, %(min_d)s) ' \
                     '  AND e.parent_geometry {cf!s} ' \
                     '  AND e.used = false ' \
                     'ORDER BY RANDOM() ' \
                     'LIMIT 1 ' \
                     'FOR UPDATE'

        while not self.q.emtpy():
            cmd = self.q.get()
            assert isinstance(cmd, PointMatchCommand)

            # Set comparison strings and tables
            if cmd.matching_type is MatchingType.within:
                cf = '= s.parent_geometry'
                tbl_s = 'within_start'
                tbl_e = 'within_end'
            else:
                # Using IN to minimize the amount of data that has to be scanned and try to use indexes efficiently
                cf = 'IN (SELECT * FROM (' \
                     '  SELECT sk.rs FROM de_shp_kreise sk ' \
                     '  INNER JOIN de_commuter_kreise ck USING (rs) ' \
                     '  WHERE ST_DWithin(s.geom::geography, sk.geom::geography, %(max_d)s) ' \
                     '  UNION ' \
                     '  SELECT sg.rs FROM de_shp_gemeinden sg ' \
                     '  INNER JOIN de_commuter_gemeinden cg USING (rs) ' \
                     '  WHERE ST_DWithin(s.geom::geography, sg.geom::geography, %(max_d)s) ' \
                     'WHERE rs != s.parent_geometry))'
                tbl_s = 'start'
                tbl_e = 'end'

            retries = 0
            while True:
                # Get the index of the corresponding category where we will try to match an end point for
                if cmd.matching_type is MatchingType.within:
                    index = self.distribution.within_idx
                else:
                    index = self.distribution.outgoing_idx

                distances = self.distribution.get_distance(cmd.matching_type, index)

                # Query the Database for a end point
                with database.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(sql_search.format(tbl_s=tbl_s, tbl_e=tbl_e, cf=cf),
                                start=cmd.point_id, **distances)

                    if cur.rowcount == 0:
                        retries += 1
                        self.logging.warning('No possible end point found for %s', cmd.point_id)
                        if retries >= self.max_retries:
                            # If after self.max_retries there is no end point found we stop searching
                            self.logging.warning('Too many retries to find end point for point id: %s', cmd.point_id)
                            # TODO decide what to do with these points
                            break
                        else:
                            # Search again
                            continue

                    # A point has been found, now check if distribution constraints are still met
                    if not self.distribution.increase(cmd.matching_type, index):
                        conn.rollback()
                        continue

                    (destination, ) = cur.fetchone()
                    cur.execute('UPDATE de_sim_points_end SET used = true WHERE used = false AND id = %s',
                                (destination, ))
                    if cur.rowcount == 0:
                        # Update did not work, rollback, find new point
                        conn.rollback()
                        continue

                    # Everything is fine so let's insert the points in the table for the routes
                    cur.execute('INSERT INTO de_sim_routes (start_point, end_point) VALUES (%s, %s)',
                                (cmd.point_id, destination,))
                    conn.commit()