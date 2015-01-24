"""
Class for Matching start and endpoints of the simulation using new PostgreSQL 9.5 SKIP LOCKED feature

Pseudo code:
    Get MatchingDistribution from queue
    Iterate over the distributions
        choose within or outgoing matching
        Select random start points
        Select random end point which should comply with distribution parameters
        Check matched points for compliance to distribution parameters
        Insert only complying points into database and mark them as used
    Update the MatchingDistribution with the yet unmatched commuters and
    if nesessary re-queue the MatchingDistribution
"""
import logging
from multiprocessing import Process, Event, Queue
import time

from database import connection
from builder.enums import MatchingType
from builder.commuter_distribution import MatchingDistribution
from helper.counter import Counter


class PointMassMatcherProcess(Process):
    """
    Point Mass Matcher Process using PostgreSQL 9.5 feature SKIP LOCKED
    """

    def __init__(self, matching_queue: Queue, counter: Counter, exit_event: Event, max_age_distribution=3):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.mq = matching_queue
        self.exit_event = exit_event
        self.counter = counter
        self.max_age_distribution = max_age_distribution

    def run(self):
        while not self.mq.empty():
            if self.exit_event.is_set():
                break

            # Get a MatchingDistribution
            md = self.mq.get()

            # Check if we got a result, otherwise stop the loop
            # Catch the stupid NoneType Error (should not happen with database anymore)
            if not isinstance(md, MatchingDistribution):
                self.logging.error('Got %s', type(md).__name__)
                time.sleep(0.1)
                continue

            self.logging.debug('Start matching points for: %12s', md.rs)
            start_time = time.time()

            # Initialize arguments for MatchingDistribution update
            within = 0
            outgoing = []
            updated = 0
            with connection.get_connection() as conn:
                cur = conn.cursor()
                for params in md:
                    # Check if there are commuters to be matched, otherwise look at the next set
                    if params['commuters'] == 0:
                        continue

                    # Select the type of matching to be done
                    if params['type'] is MatchingType.within:
                        '''Match within'''
                        sql = 'SELECT s.id AS start, e.id AS destination ' \
                              'FROM ( ' \
                              '  SELECT id, geom, row_number() over() as i FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_s!s} ' \
                              '    WHERE parent_geometry {cf!s} AND NOT used' \
                              '    ORDER BY RANDOM() ' \
                              '    FOR UPDATE SKIP LOCKED' \
                              '  ) AS sq ' \
                              ') AS s ' \
                              'INNER JOIN ( ' \
                              '  SELECT id, geom, row_number() over() as i FROM ( ' \
                              '    SELECT id, geom ' \
                              '    FROM de_sim_points_{tbl_e!s} ' \
                              '    WHERE parent_geometry {cf!s}  AND NOT used' \
                              '    ORDER BY RANDOM() ' \
                              '    FOR UPDATE SKIP LOCKED' \
                              '  ) AS t ' \
                              ') AS e ' \
                              'ON s.i = e.i AND NOT ST_DWithin(s.geom, e.geom, %(min_d)s)'
                        tbl_s = 'within_start'
                        tbl_e = 'within_end'
                        tbl_r = 'within'
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
                              '    FOR UPDATE SKIP LOCKED' \
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
                              '    FOR UPDATE SKIP LOCKED' \
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
                        tbl_r = 'outgoing'
                        cf = 'IN (' + cf + ')'

                    # Match the points and save them
                    upsert = 'WITH points AS (' + sql + '), ' \
                             'upsert_start AS (UPDATE de_sim_points_{tbl_s!s} ps SET used = true FROM points p WHERE p.start = ps.id), ' \
                             'upsert_destination AS (UPDATE de_sim_points_{tbl_e!s} pe SET used = true FROM points p WHERE p.destination = pe.id) ' \
                             'INSERT INTO de_sim_routes_{tbl_r!s} (start_point, end_point) SELECT start, destination FROM points'
                    cur.execute(upsert.format(tbl_e=tbl_e, tbl_s=tbl_s, cf=cf, tbl_r=tbl_r), params)
                    conn.commit()

                    # Update MatchingDistribution arguments
                    updated += cur.rowcount
                    commuters = params['commuters'] - cur.rowcount
                    if params['type'] is MatchingType.within:
                        within = commuters
                    else:
                        outgoing.append(commuters)

                # Check if MatchingDistribution has reached its max age
                if md.age < self.max_age_distribution and sum(outgoing) + within > 0:
                    md.reuse(within, outgoing)
                    self.mq.put(md)
                count = self.counter.increment()

                self.logging.info('(%4d/%d) Finished matching %6d points for %12s in %.2f',
                                  count, self.counter.maximum, updated,
                                  md.rs, time.time() - start_time)
        self.logging.info('Exiting Matcher Tread: %s', self.name)