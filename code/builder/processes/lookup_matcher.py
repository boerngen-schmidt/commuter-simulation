import logging
import time
import multiprocessing as mp

from builder.commuter_distribution import MatchingDistribution
from builder.enums import MatchingType, PointType
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
            # TODO Create new MatchingDistirbution
            if not isinstance(md, MatchingDistribution):
                self.logging.error('Got %s', type(md).__name__)
                time.sleep(0.1)
                continue
            start_time = time.time()

            with db.get_connection() as conn:
                cur = conn.cursor()
                for params in md:
                    # SELECT the lookup points to a given rs
                    sql = 'SELECT id FROM de_sim_points_lookup WHERE rs = %(rs)s AND type = %(p_type)s ORDER BY RANDOM()'
                    args = dict(rs=md.rs, p_type=params['type'].value)
                    cur.execute(sql, args)
                    result = cur.fetchall()
                    conn.commit()
                for lookup in result:
                    self._lookup_match_within(lookup[0])
                    self._lookup_match_outgoing(lookup[0])

    def _lookup_match_within(self, lookup_id, rs):
        sql = 'WITH reachable AS (' \
              '  SELECT id FROM de_sim_points_lookup ' \
              '  WHERE type = %(end_type)s AND rs = %(rs)s ' \
              '   AND NOT ST_DWithin(geom_meter, (SELECT geom_meter FROM de_sim_points_lookup WHERE id = %(lookup)s), %(distance)s)), ' \
              ' amount AS (SELECT SUM(*) FROM de_sim_points_within_start WHERE lookup = %(lookup)s)' \
              'SELECT s.id AS start, e.id AS destination ' \
              'FROM ( ' \
              '  SELECT id, row_number() over() as i FROM ( ' \
              '    SELECT id ' \
              '    FROM de_sim_points_within_start ' \
              '    WHERE lookup = %(lookup)s AND NOT used' \
              '    ORDER BY RANDOM() ' \
              '	   LIMIT %(amount)s' \
              '    FOR UPDATE SKIP LOCKED' \
              '  ) AS sq ' \
              ') AS s ' \
              'INNER JOIN ( ' \
              '  SELECT id, row_number() over() as i FROM ( ' \
              '    SELECT id ' \
              '    FROM de_sim_points_within_end ' \
              '    WHERE NOT used AND lookup IN (SELECT * FROM reachable)' \
              '    ORDER BY RANDOM()' \
              '	   LIMIT %(amount)s' \
              '    FOR UPDATE SKIP LOCKED' \
              '  ) AS t ' \
              ') AS e ' \
              'ON s.i = e.i'

        args = dict(end_type='within_end', distance=2000, lookup=lookup_id, rs=rs)
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, args)


        def _lookup_match_outgoing(self, lookup_id):
            pass