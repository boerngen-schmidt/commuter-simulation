import logging
from queue import Empty
import time

from builder.commuter_distribution import MatchingDistributionRevised
from builder.enums import MatchingType
from helper.counter import Counter
from database import connection as db


__author__ = 'benjamin'

import multiprocessing as mp


class PointMatcherRevised(mp.Process):
    def __init__(self, matching_queue: mp.Queue, counter: Counter, exit_event: mp.Event):
        super().__init__()
        self.q = matching_queue
        self.counter = counter
        self.exit_event = exit_event
        self.log = logging.getLogger(self.name)

    def run(self):
        while True:
            try:
                md = self.q.get(timeout=1)
            except Empty:
                if self.exit_event.is_set():
                    break
                else:
                    continue
            else:
                if not md or self.exit_event.is_set():
                    break

            assert isinstance(md, MatchingDistributionRevised)
            start_time = time.time()
            sql = 'WITH start_points AS (SELECT id, geom, row_number() over() as i FROM (SELECT id, geom FROM de_sim_points_{tbl_s!s} WHERE NOT used AND rs = %(rs)s ORDER BY RANDOM() LIMIT %(limit)s FOR UPDATE SKIP LOCKED) AS sp), ' \
                  '     start_centroid AS (SELECT ST_Centroid(ST_Collect(Array(SELECT geom FROM start_points)))), ' \
                  '     end_points AS (SELECT id, geom, row_number() over() as i FROM ( ' \
                  '       SELECT id, geom FROM de_sim_points_{tbl_e!s} WHERE NOT used AND rs {reachable!s} ' \
                  '       LIMIT %(limit)s FOR UPDATE SKIP LOCKED) as ep), ' \
                  '     upsert_start AS (UPDATE de_sim_points_{tbl_s!s} ps SET used = true FROM start_points p WHERE p.id = ps.id), ' \
                  '     upsert_destination AS (UPDATE de_sim_points_{tbl_e!s} pe SET used = true FROM end_points p WHERE p.id = pe.id) ' \
                  'INSERT INTO de_sim_routes_{tbl_r!s} (start_point, end_point, distance_meter)  ' \
                  'SELECT s.id AS start, e.id AS destination, ST_Distance(s.geom::geography, e.geom::geography) AS distance_meter FROM start_points s INNER JOIN end_points e USING(i) '

            if md.matching_type is MatchingType.outgoing:
                tbl_s = 'start'
                tbl_e = 'end'
                tbl_r = 'outgoing'
                reachable = 'IN (' \
                            ' WITH ZeGeom as (SELECT ST_Union(geom) FROM de_shp_{tbl_shp!s} WHERE rs = %(rs)s) ' \
                            '  SELECT sk.rs FROM de_commuter_kreise ck  ' \
                            '    INNER JOIN de_shp_kreise sk ON sk.rs=ck.rs ' \
                            '    WHERE ST_Buffer((SELECT * FROM ZeGeom)::geography, %(max_d)s, \'quad_segs=2\') && sk.geom::geography' \
                            '  UNION ALL ' \
                            '  SELECT sg.rs FROM de_commuter_gemeinden cg  ' \
                            '    INNER JOIN de_shp_gemeinden sg ON sg.rs=cg.rs ' \
                            '    WHERE ST_Buffer((SELECT * FROM ZeGeom)::geography, %(max_d)s, \'quad_segs=2\') && sg.geom::geography) ' \
                            'AND ST_Contains(ST_Buffer((SELECT * FROM start_centroid)::geography, %(max_d)s, \'quad_segs=2\'), geom::geography) ' \
                            'AND NOT ST_Contains(ST_Buffer((SELECT * FROM start_centroid)::geography, %(min_d)s, \'quad_segs=2\'), geom::geography) '
                if len(md.rs) == 12:
                    tbl_shp = 'gemeinden'
                else:
                    tbl_shp = 'kreise'

                reachable = reachable.format(tbl_shp=tbl_shp)
            else:
                tbl_s = 'within_start'
                tbl_e = 'within_end'
                tbl_r = 'within'
                reachable = '= %(rs)s'

            sql = sql.format(tbl_s=tbl_s, tbl_e=tbl_e, tbl_r=tbl_r, reachable=reachable)

            with db.get_connection() as conn:
                cur = conn.cursor()
                args = dict(rs=md.rs, max_d=md.max_d, min_d=md.min_d, limit=md.commuter)
                cur.execute(sql, args)
                updated = cur.rowcount
                conn.commit()

            count = self.counter.increment()
            self.log.info('(%5d/%d) Finished matching %8s %6d/%6d points for %12s in %.2f',
                         count, self.counter.maximum, md.matching_type.value, updated, md.commuter, md.rs, time.time() - start_time)