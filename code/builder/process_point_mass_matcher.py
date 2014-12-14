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
import time

from helper import database
from helper.commuter_distribution import MatchingDistribution
from helper.counter import Counter


class PointMassMatcherProcess(Process):
    """
    Point Matcher Process

    Spawns Threads which do the actual matching
    """

    def __init__(self, district_queue: Queue, insert_queue, counter: Counter):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.dq = district_queue
        self.insert_q = insert_queue
        self.counter = counter

    def run(self):
        while not self.dq.empty():
            current_dist = self.dq.get()
            assert isinstance(current_dist, MatchingDistribution)
            current_rs = current_dist.rs
            start_time = time.time()
            with database.get_connection() as conn:
                cur = conn.cursor()
                '''Match within'''
                sql_search = 'SELECT s.id AS start, e.id AS destination ' \
                             'FROM ( ' \
                             '    SELECT id, geom, row_number() over() as i FROM ( ' \
                             '		SELECT id, geom ' \
                             '		FROM de_sim_points_{tbl_s!s} ' \
                             '		WHERE parent_geometry {cf!s} ' \
                             '		ORDER BY RANDOM() ' \
                             '      FOR UPDATE ' \
                             '	) AS sq ' \
                             ') AS s ' \
                             'INNER JOIN ( ' \
                             '    SELECT id, geom, row_number() over() as i ' \
                             '    FROM ( ' \
                             '		SELECT id, geom ' \
                             '		FROM de_sim_points_{tbl_e!s} ' \
                             '		WHERE parent_geometry {cf!s} ' \
                             '		ORDER BY RANDOM() ' \
                             '      FOR UPDATE ' \
                             '    ) AS t ' \
                             ') AS e ' \
                             'ON s.i = e.i ' \
                             'WHERE NOT ST_DWithin(s.geom, e.geom, 2000) '
                tbl_s = 'within_start'
                tbl_e = 'within_end'
                cf = '= %(rs)s'
                sql_reachable_rs = 'SELECT sk.rs FROM de_commuter_kreise ck ' \
                                   'INNER JOIN de_shp_kreise sk ON sk.rs=ck.rs AND ST_DWithin((SELECT geom FROM de_shp_kreise WHERE rs = %(rs)s), sk.geom, %(max_d)s) ' \
                                   'UNION  ' \
                                   'SELECT cg.rs FROM de_commuter_gemeinden cg  ' \
                                   'INNER JOIN de_shp_gemeinden sg ON sg.rs=cg.rs AND ST_DWithin((SELECT geom FROM de_shp_kreise WHERE rs = %(rs)s), sg.geom, %(max_d)s) '
                cur.execute(sql_search.format(tbl_e=tbl_e, tbl_s=tbl_s, cf=cf), {'rs': current_rs})
                for (start, destination) in cur.fetchall():
                    self.insert_q.put('EXECUTE de_sim_routes_within_plan ({start!s}, {destination!s});'.format(start=start, destination=destination))
                    cur.execute('UPDATE de_sim_points_within_start SET used = true WHERE id=%s AND NOT used', (start, ))
                    cur.execute('UPDATE de_sim_points_within_end SET used = true WHERE id=%s AND NOT used',
                                (destination, ))

                conn.commit()
                self.counter.increment()
                self.logging.info('(%4d/%d) Finished matching within points for %s in %s',
                                  self.counter.value, self.counter.max,
                                  current_rs, time.time() - start_time)