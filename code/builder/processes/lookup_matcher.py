import logging
import time
import multiprocessing as mp

from builder.commuter_distribution import MatchingDistribution
from helper.counter import Counter
import database.connection as db


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
#TODO Create new MatchingDistirbution
            if not isinstance(md, MatchingDistribution):
                self.logging.error('Got %s', type(md).__name__)
                time.sleep(0.1)
                continue
            start_time = time.time()

            with db.get_connection() as conn:
                cur = conn.cursor()
                for params in md:
                    sql = 'SELECT * FROM de_sim_points_lookup WHERE rs = %(rs)s AND type = %(p_type)s'
                    args = dict(rs=md.rs, p_type=params['type'].value)
                    cur.execute(sql, args)
                    for lookup in cur.fetchall():
                        sql = 'SELECT *'
