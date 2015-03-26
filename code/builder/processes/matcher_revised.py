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
        super().__init__(name='PMR')
        self.q = matching_queue
        self.counter = counter
        self.exit_event = exit_event
        self.log = logging.getLogger(self.name)

    def run(self):
        upsert_match_info = 'WITH ' \
                            '  vals(rs, max_d, min_d, done, total) AS (VALUES (%(rs)s, %(max_d)s, %(min_d)s, %(done)s, %(limit)s)),' \
                            '  upsert AS ( ' \
                            '    UPDATE de_sim_data_matching_info ' \
                            '    SET done = %(done)s, total = %(limit)s ' \
                            '    WHERE rs = %(rs)s AND max_d = %(max_d)s AND min_d = %(min_d)s ' \
                            '    RETURNING rs, max_d, min_d ' \
                            '  ) ' \
                            'INSERT INTO de_sim_data_matching_info ' \
                            '  SELECT * FROM vals WHERE NOT EXISTS(' \
                            '    SELECT 1 FROM upsert WHERE rs = %(rs)s AND max_d = %(max_d)s AND min_d = %(min_d)s)'
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
            sql = 'WITH  ' \
                  '  points AS ({points!s}), ' \
                  '  upsert_start AS (' \
                  '     UPDATE de_sim_points_{tbl_s!s} ps SET used = TRUE FROM points p WHERE p.start = ps.id),' \
                  '  upsert_destination AS (' \
                  '     UPDATE de_sim_points_{tbl_e!s} pe SET used = TRUE FROM points p WHERE p.destination = pe.id)' \
                  'INSERT INTO de_sim_routes_{tbl_r!s} (start_point, end_point, distance_meter) ' \
                  '  SELECT start, destination, distance_meter FROM points; '

            if md.matching_type is MatchingType.outgoing:
                tbl_s = 'start'
                tbl_e = 'end'
                tbl_r = 'outgoing'
                points = 'SELECT ' \
                         '  s.id AS start, ' \
                         '  e.id AS destination, ' \
                         '  ST_Distance(s.geom, e.geom) as distance_meter ' \
                         'FROM ( ' \
                         '  SELECT id, geom, row_number() OVER () AS i  ' \
                         '  FROM ( ' \
                         '    SELECT id, geom  ' \
                         '    FROM de_sim_points_start ' \
                         '    WHERE  ' \
                         '      NOT used  ' \
                         '      AND rs = %(rs)s  ' \
                         '    ORDER BY RANDOM()  ' \
                         '    LIMIT %(limit)s  ' \
                         '    FOR UPDATE SKIP LOCKED ' \
                         '  ) AS sq ' \
                         ') AS s  ' \
                         'INNER JOIN ( ' \
                         '  SELECT id, geom, row_number() OVER () AS i  ' \
                         '  FROM ( ' \
                         '    SELECT id, geom  ' \
                         '    FROM de_sim_points_end ' \
                         '    WHERE  ' \
                         '      NOT used  ' \
                         '      AND rs IN ( ' \
                         '        SELECT sk.rs  ' \
                         '        FROM de_commuter_kreise ck  ' \
                         '          INNER JOIN de_shp_kreise sk  ' \
                         '            ON sk.rs = ck.rs AND ST_DWithin((SELECT ST_Union(geom) FROM de_shp WHERE rs = %(rs)s), sk.geom, %(max_d)s) ' \
                         '        UNION  ' \
                         '        SELECT cg.rs  ' \
                         '        FROM de_commuter_gemeinden cg  ' \
                         '          INNER JOIN de_shp_gemeinden sg  ' \
                         '            ON sg.rs = cg.rs AND ST_DWithin((SELECT ST_Union(geom) FROM de_shp WHERE rs = %(rs)s), sg.geom, %(max_d)s) ' \
                         '        ) ' \
                         '    LIMIT %(limit)s  ' \
                         '    FOR UPDATE SKIP LOCKED ' \
                         '  ) AS t ' \
                         ') AS e ON s.i = e.i AND NOT ST_DWithin(s.geom, e.geom, %(min_d)s)  ' \
                         '          AND ST_DWithin(s.geom, e.geom, %(max_d)s) '
            else:
                tbl_s = 'within_start'
                tbl_e = 'within_end'
                tbl_r = 'within'
                points = 'SELECT ' \
                         '  s.id AS start, ' \
                         '  e.id AS destination, ' \
                         '  ST_Distance(s.geom, e.geom) as distance_meter ' \
                         'FROM ( ' \
                         '  SELECT id, geom, row_number() OVER () AS i  ' \
                         '  FROM ( ' \
                         '    SELECT id, geom  ' \
                         '    FROM de_sim_points_within_start ' \
                         '    WHERE  ' \
                         '      NOT used  ' \
                         '      AND rs = %(rs)s  ' \
                         '    ORDER BY RANDOM()  ' \
                         '    LIMIT %(limit)s  ' \
                         '    FOR UPDATE SKIP LOCKED ' \
                         '  ) AS sq ' \
                         ') AS s  ' \
                         'INNER JOIN ( ' \
                         '  SELECT id, geom, row_number() OVER () AS i  ' \
                         '  FROM ( ' \
                         '    SELECT id, geom  ' \
                         '    FROM de_sim_points_within_end ' \
                         '    WHERE  ' \
                         '      NOT used  ' \
                         '      AND rs = %(rs)s '\
                         '    LIMIT %(limit)s  ' \
                         '    FOR UPDATE SKIP LOCKED ' \
                         '  ) AS t ' \
                         ') AS e ON s.i = e.i AND NOT ST_DWithin(s.geom, e.geom, %(min_d)s)  '

            sql = sql.format(tbl_e=tbl_e, tbl_s=tbl_s, tbl_r=tbl_r, points=points)

            with db.get_connection() as conn:
                cur = conn.cursor()
                args = dict(rs=md.rs, max_d=md.max_d, min_d=md.min_d, limit=md.commuter)
                cur.execute(sql, args)
                updated = cur.rowcount
                args['done'] = updated
                cur.execute(upsert_match_info, args)
                conn.commit()
                rows = cur.rowcount
            time.sleep(0.0001 * rows)

            count = self.counter.increment()
            self.log.info('(%5d/%d) Finished matching %8s (min: %6d, max: %6d) %6d/%6d points for %12s in %.2f',
                          count, self.counter.maximum, md.matching_type.value.ljust(8),md.min_d, md.max_d,
                          updated, md.commuter, md.rs, time.time() - start_time)
