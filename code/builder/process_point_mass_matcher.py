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
import time
from queue import Empty

from builder import MatchingType
from helper import database
from helper.commuter_distribution import MatchingDistribution
from helper.counter import Counter


class PointMassMatcherProcess(Process):
    """
    Point Matcher Process

    Spawns Threads which do the actual matching
    """

    def __init__(self, district_queue, insert_queue, counter: Counter):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.dq = district_queue
        self.insert_q = insert_queue
        self.counter = counter

    def run(self):
        while not self.dq.empty():
            try:
                current_dist = self.dq.get(timeout=1)
            except Empty:
                continue
            assert isinstance(current_dist, MatchingDistribution)
            current_rs = current_dist.rs
            start_time = time.time()

            within = 0
            outgoing = []

            with database.get_connection() as conn:
                cur = conn.cursor()
                for params in current_dist:
                    if params['commuter'] == 0:
                        continue

                    if params['type'] is MatchingType.within:
                        '''Match within'''
                        sql = 'SELECT s.id AS start, e.id AS destination ' \
                              'FROM ( ' \
                              '  SELECT id, geom, row_number() over() as i FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_s!s} ' \
                              '    WHERE parent_geometry {cf!s} ' \
                              '    ORDER BY RANDOM() ' \
                              '  ) AS sq ' \
                              ') AS s ' \
                              'INNER JOIN ( ' \
                              '  SELECT id, geom, row_number() over() as i FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_e!s} ' \
                              '    WHERE parent_geometry {cf!s} ' \
                              '    ORDER BY RANDOM() ' \
                              '  ) AS t ' \
                              ') AS e ' \
                              'ON s.i = e.i AND NOT ST_DWithin(s.geom, e.geom, %(min_d));'
                        tbl_s = 'within_start'
                        tbl_e = 'within_end'
                        cf = '= %(rs)s'
                    else:
                        '''Matching outgoing'''
                        sql = 'SELECT s.id AS start, e.id AS destination ' \
                              'FROM ( ' \
                              '  SELECT id, geom, row_number() over() as i FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_s!s} ' \
                              '    WHERE parent_geometry = %(rs)s AND NOT used' \
                              '    ORDER BY RANDOM() ' \
                              '    LIMIT %(commuters)s ' \
                              '  ) AS sq ' \
                              ') AS s ' \
                              'INNER JOIN ( ' \
                              '  SELECT id, geom, row_number() over() as i ' \
                              '  FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_e!s} ' \
                              '    WHERE parent_geometry {cf!s} AND NOT used' \
                              '    ORDER BY RANDOM() ' \
                              '    LIMIT %(commuters)s ' \
                              '  ) AS t ' \
                              ') AS e ' \
                              'ON s.i = e.i ' \
                              'WHERE NOT ST_DWithin(s.geom, e.geom, %(min_d)s) AND ST_DWithin(s.geom, e.geom, %(max_d)s)'
                        cf = 'SELECT sk.rs FROM de_commuter_kreise ck ' \
                             'INNER JOIN de_shp_kreise sk ON sk.rs=ck.rs AND ST_DWithin(' \
                             '  (SELECT ST_Union(geom) FROM de_shp_kreise WHERE rs = %(rs)s), sk.geom, %(max_d)s) ' \
                             'UNION  ' \
                             'SELECT cg.rs FROM de_commuter_gemeinden cg  ' \
                             'INNER JOIN de_shp_gemeinden sg ON sg.rs=cg.rs AND ST_DWithin(' \
                             '  (SELECT ST_Union(geom) FROM de_shp_gemeinden WHERE rs = %(rs)s), sg.geom, %(max_d)s)'
                        tbl_s = 'start'
                        tbl_e = 'end'
                        cf = 'IN (' + cf + ')'

                    cur.execute(sql.format(tbl_e=tbl_e, tbl_s=tbl_s, cf=cf), params)

                    commuters = params['commuters'] - cur.rowcount
                    if params['type'] is MatchingType.within:
                        within = commuters
                    else:
                        outgoing.append(commuters)

                    for (s_id, d_id) in cur.fetchall():
                        self.insert_q.put(
                            'EXECUTE de_sim_routes_within_plan ({s_id!s}, {d_id!s});'.format(s_id=s_id, d_id=d_id))
                        cur.execute(
                            'UPDATE de_sim_points_{tbl_s!s} SET used = true WHERE id=%s AND NOT used'.format(
                                tbl_s=tbl_s), (s_id, ))
                        cur.execute(
                            'UPDATE de_sim_points_{tbl_e!s} SET used = true WHERE id=%s AND NOT used'.format(
                                tbl_e=tbl_e), (d_id, ))
                    conn.commit()

                if current_dist.age < self.max_age_distribution:
                    self.dq.put(current_dist.reuse(within, outgoing))
                    count = self.counter.increment_both()
                else:
                    count = self.counter.increment()
                self.logging.info('(%4d/%d) Finished matching points for %s in %s',
                                  count, self.counter.max,
                                  current_rs, time.time() - start_time)
        self.logging.info('Exiting Matcher Tread: %s', self.name)