import logging
import time
import multiprocessing as mp

from builder.enums import PointType
from helper.counter import Counter
import database.connection as db


commuter_distribution = {'01': (0.367, 0.196, 0.252, 0.131, 0.054),
                         '02': (0.260, 0.320, 0.341, 0.065, 0.015),
                         '03': (0.329, 0.205, 0.271, 0.145, 0.050),
                         '04': (0.316, 0.325, 0.259, 0.061, 0.039),
                         '05': (0.310, 0.229, 0.282, 0.135, 0.044),
                         '06': (0.288, 0.199, 0.304, 0.158, 0.052),
                         '07': (0.303, 0.185, 0.285, 0.163, 0.065),
                         '08': (0.338, 0.212, 0.297, 0.118, 0.035),
                         '09': (0.321, 0.194, 0.300, 0.134, 0.051),
                         '10': (0.243, 0.209, 0.332, 0.171, 0.045),
                         '11': (0.224, 0.303, 0.372, 0.084, 0.017),
                         '12': (0.301, 0.160, 0.255, 0.209, 0.075),
                         '13': (0.348, 0.184, 0.235, 0.147, 0.087),
                         '14': (0.338, 0.239, 0.276, 0.108, 0.039),
                         '15': (0.334, 0.205, 0.254, 0.136, 0.070),
                         '16': (0.367, 0.196, 0.252, 0.131, 0.054)}

commuting_distance = ({'min_d': 2000, 'max_d': 5000},
                      {'min_d': 5000, 'max_d': 10000},
                      {'min_d': 10000, 'max_d': 25000},
                      {'min_d': 25000, 'max_d': 50000},
                      {'min_d': 50000, 'max_d': 140000})


class PointLookupMatcherProcess(mp.Process):
    def __init__(self, matching_queue: mp.Queue, counter: Counter, exit_event: mp.Event):
        super().__init__()
        self.q = matching_queue
        self.counter = counter
        self.exit_event = exit_event
        self.logging = logging.getLogger(self.name)

    def run(self):
        while True:
            md = self.q.get()
            if not md or self.exit_event.is_set():
                break
            start_time = time.time()
            updated = dict(outgoing=0, within=0)
            # Do Matching for each point type
            for p_start, p_end in zip((PointType.Start, PointType.Within_Start), (PointType.End, PointType.Within_End)):
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    # SELECT the lookup points to a given rs
                    sql = 'SELECT id FROM de_sim_points_lookup WHERE rs = %(rs)s AND type = %(p_type)s ORDER BY RANDOM()'
                    args = dict(rs=md.rs, p_type=p_start.value)
                    cur.execute(sql, args)
                    result = cur.fetchall()
                    conn.commit()
                    matched_points = 0
                    for lookup in result:
                        matched_points += self._lookup_match(lookup[0], md.rs, p_start, p_end)
                    if p_start is PointType.Start:
                        updated['outgoing'] = matched_points
                    else:
                        updated['within'] = matched_points
            count = self.counter.increment()
            self.logging.info('(%4d/%d) Finished matching for %12s in %.2f. Outgoing (%6d/%6d). Within (%6d/%6d).',
                              count, self.counter.maximum, md.rs, time.time() - start_time,
                              updated['outgoing'], md.outgoing, updated['within'], md.within)
        self.logging.info('Exiting Matcher Tread: %s', self.name)

    def _lookup_match(self, lookup_id, rs, p_start, p_end):
        if p_start is PointType.Start:
            reachable = 'SELECT id FROM de_sim_points_lookup WHERE type = %(end_type)s AND rs != %(rs)s ' \
                        'AND NOT ST_DWithin(geom_meter, (SELECT geom_meter FROM de_sim_points_lookup WHERE id = %(lookup)s), %(d_min)s)' \
                        'AND ST_DWithin(geom_meter, (SELECT geom_meter FROM de_sim_points_lookup WHERE id = %(lookup)s), %(d_max)s)'
            tbl_r = 'outgoing'
            limit = 'ROUND((SELECT * FROM amount) * %(percent)s)'
        elif p_start is PointType.Within_Start:
            reachable = 'SELECT id FROM de_sim_points_lookup WHERE type = %(end_type)s AND rs = %(rs)s ' \
                        'AND NOT ST_DWithin(geom_meter, (SELECT geom_meter FROM de_sim_points_lookup WHERE id = %(lookup)s), %(d_min)s)'
            tbl_r = 'within'
            limit = '(SELECT * FROM amount)'
        else:
            logging.error('No PointType was given')
            return

        sql = 'WITH reachable AS ({reachable!s}), ' \
              ' amount AS (SELECT SUM(*) FROM de_sim_points_within_start WHERE lookup = %(lookup)s),' \
              ' points AS (SELECT s.id AS start, e.id AS destination FROM ( ' \
              '             SELECT id, row_number() over() as i FROM ( ' \
              '               SELECT id ' \
              '               FROM de_sim_points_{tbl_s!s} ' \
              '               WHERE lookup = %(lookup)s AND NOT used' \
              '               ORDER BY RANDOM() ' \
              '           	   LIMIT {limit!s}' \
              '               FOR UPDATE SKIP LOCKED' \
              '             ) AS sq ' \
              '           ) AS s ' \
              '           INNER JOIN ( ' \
              '             SELECT id, row_number() over() as i FROM ( ' \
              '               SELECT id ' \
              '               FROM de_sim_points_{tbl_e!s} ' \
              '               WHERE NOT used AND lookup IN (SELECT * FROM reachable)' \
              '               ORDER BY RANDOM()' \
              '           	   LIMIT {limit!s}' \
              '               FOR UPDATE SKIP LOCKED' \
              '             ) AS t ' \
              '           ) AS e ON s.i = e.i' \
              ' upsert_start AS (UPDATE de_sim_points_{tbl_s!s} ps SET used = true FROM points p WHERE p.start = ps.id), ' \
              ' upsert_destination AS (UPDATE de_sim_points_{tbl_e!s} pe SET used = true FROM points p WHERE p.destination = pe.id) ' \
              'INSERT INTO de_sim_routes_{tbl_r!s} (start_point, end_point) SELECT start, destination FROM points'
        sql = sql.format(tbl_s=p_start.value, tbl_e=p_end.value, tbl_r=tbl_r, reachable=reachable, limit=limit)

        updated = 0
        if p_start is PointType.Start:
            for distances, percent in zip(commuting_distance, commuter_distribution[rs[:2]]):
                args = dict(rs=rs, lookup=lookup_id, end_type=p_end.value, percent=percent)
                args.update(distances)
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(sql, args)
                    conn.commit()
                    updated = cur.rowcount
        elif p_start is PointType.Within_Start:
            args = dict(end_type=p_end.value, d_min=2000, lookup=lookup_id, rs=rs)
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, args)
                conn.commit()
                updated = cur.rowcount
        return updated