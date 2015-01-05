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
from multiprocessing import Process
from threading import Thread
from queue import Queue as ThreadQueue
import time

from database import connection
from builder import MatchingType
from builder.commands import PointMatchCommand
from matching.commuter_distribution import MatchingDistribution


class PointMatcherProcess(Process):
    """
    Point Matcher class
    """

    def __init__(self, district_queue, insert_queue):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.dq = district_queue
        self.cmd_q = ThreadQueue()
        self.matcher_threads = 3
        self.insert_q = insert_queue

    def run(self):
        while not self.dq.empty():
            start = time.time()
            current_dist = self.dq.get()
            assert isinstance(current_dist, MatchingDistribution)
            data = current_dist.next()

            self.logging.info('Start matching (%s/%s) for %s', current_dist.index, len(current_dist), current_dist.rs)
            self.fill_command_queue(current_dist)

            threads = []
            for i in range(self.matcher_threads):
                name = 'Matcher Thread %s' % i
                t = PointMatcherThread(self.cmd_q, self.insert_q)
                t.setName(name)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            end = time.time()
            self.logging.info('Finished matching (%s, %s) in category (%s/%s) for %s in %s seconds',
                              data['within']['commuters'], data['outgoing']['commuters'],
                              current_dist.index, len(current_dist),
                              current_dist.rs, (end - start))
            if current_dist.has_next():
                # Still categories to do, enqueue again
                self.dq.put(current_dist)

    def fill_command_queue(self, current_dist):
        """
        Adds PointMatchCommand elements to the queue for which a destination should be matched

        :param rs: current Regionalschlüssel
        :param within: number of commuters within the rs
        :param outgoing: number of commuters leaving the rs
        :return: None
        """
        with connection.get_connection() as conn:
            cur = conn.cursor()

            cur.execute('SELECT id, ST_AsEWKB(geom) AS geom '
                        'FROM de_sim_points_within_start '
                        'WHERE parent_geometry = %s AND NOT used '
                        'ORDER BY RANDOM() LIMIT %s', (current_dist.rs, current_dist.commuter_within,))
            conn.commit()
            [self.cmd_q.put(
                PointMatchCommand(p[0], current_dist.rs, current_dist.data['within'], MatchingType.within, p[1]))
             for p in cur.fetchall()]

            cur.execute('SELECT id, ST_AsEWKB(geom) AS geom '
                        'FROM de_sim_points_start '
                        'WHERE parent_geometry = %s AND NOT used '
                        'ORDER BY RANDOM() LIMIT %s', (current_dist.rs, current_dist.commuter_outgoing,))
            conn.commit()
            [self.cmd_q.put(
                PointMatchCommand(p[0], current_dist.rs, current_dist.data['outgoing'], MatchingType.outgoing, p[1]))
             for p in cur.fetchall()]


class PointMatcherThread(Thread):
    def __init__(self, cmd_queue, insert_queue):
        """

        :param cmd_queue: Queue with PointMatchCommand
        :param insert_queue: Queue for SQL Execute Statements
        :param distribution: Commuting distance distribution
        :return:
        """
        Thread.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.max_retries = 2
        self.cmd_q = cmd_queue
        self.insert_q = insert_queue

    def run(self):
        sql_search = 'SELECT e.id AS destination ' \
                     'FROM de_sim_points_{tbl_e!s} AS e ' \
                     'WHERE {dist!s} ' \
                     '  AND e.parent_geometry {cf!s} ' \
                     '  AND NOT e.used ' \
                     'ORDER BY RANDOM() ' \
                     'LIMIT 1 ' \
                     'FOR UPDATE'
        sql_update = 'UPDATE de_sim_points_{tbl!s} SET used = true WHERE used = false AND id = %s'

        assert isinstance(self.cmd_q, ThreadQueue)
        while not self.cmd_q.empty():
            cmd = self.cmd_q.get()
            assert isinstance(cmd, PointMatchCommand)

            # Set comparison strings and tables
            if cmd.matching_type is MatchingType.within:
                dist = 'NOT ST_DWithin(ST_GeomFromEWKB(%(geom)s), e.geom, 2000)'
                cf = '= %(rs)s'
                tbl_s = 'within_start'
                tbl_e = 'within_end'
            else:
                # Using IN to minimize the amount of data that has to be scanned and try to use indexes efficiently
                dist = 'ST_DWithin(ST_GeomFromEWKB(%(geom)s), e.geom, %(max_d)s) ' \
                       '  AND NOT ST_DWithin(ST_GeomFromEWKB(%(geom)s), e.geom, %(min_d)s)'
                cf = 'IN (SELECT rs FROM (' \
                     '  SELECT sk.rs FROM de_shp_kreise sk ' \
                     '  INNER JOIN de_commuter_kreise ck USING (rs) ' \
                     '  WHERE ST_DWithin(ST_GeomFromEWKB(%(geom)s), sk.geom, %(max_d)s) ' \
                     '  UNION ' \
                     '  SELECT sg.rs FROM de_shp_gemeinden sg ' \
                     '  INNER JOIN de_commuter_gemeinden cg USING (rs) ' \
                     '  WHERE ST_DWithin(ST_GeomFromEWKB(%(geom)s), sg.geom, %(max_d)s)) reachable_rs ' \
                     'WHERE rs != %(rs)s)'
                tbl_s = 'start'
                tbl_e = 'end'

            retries = 0
            while True:
                # Get the index of the corresponding category where we will try to match an end point for
                if cmd.matching_type is MatchingType.within:
                    sql_insert = 'EXECUTE de_sim_routes_within_plan ({start!s}, {end!s});'
                else:
                    sql_insert = 'EXECUTE de_sim_routes_outgoing_plan ({start!s}, {end!s});'

                # Query the Database for a end point
                with connection.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(sql_search.format(tbl_s=tbl_s, tbl_e=tbl_e, cf=cf, dist=dist), cmd.data)

                    if cur.rowcount == 0:
                        self.logging.debug('No possible end point found for %s', cmd.point_id)
                        if retries >= self.max_retries:
                            # If after self.max_retries there is no end point found we stop searching
                            self.logging.debug('Too many retries to find end point for point id: %s', cmd.point_id)
                            # TODO decide what to do with these points
                            break
                        else:
                            retries += 1
                            # Search again
                            continue

                    (destination, ) = cur.fetchone()
                    update_error = False
                    for cur_tbl, cur_point in zip([tbl_s, tbl_e], [cmd.point_id, destination]):
                        cur.execute(sql_update.format(tbl=cur_tbl), (cur_point, ))
                        if cur.rowcount == 0:
                            # Update did not work, rollback, find new point
                            self.logging.warning("Update for table '...%s' failed on point %s", cur_tbl, cur_point)
                            self.logging.info('%s', cur.query)
                            conn.rollback()
                            update_error = True
                            break
                    if update_error:
                        break

                    # Everything is fine so let's insert the points in the table for the routes
                    self.insert_q.put(sql_insert.format(start=cmd.point_id, end=destination))
                    conn.commit()
                break