"""
Samples commuter from already matched routes to have a smaller subset to simulate

The sampler tries to have a minimum of 100 commuters per distance on outgoing commuters and 100 on within commuters.
"""
import logging
from multiprocessing import Process
import time
from queue import Empty

from database import connection
from builder.commuter_distribution import commuter_distribution, commuting_distance


'''Calculate points to match'''
n = 10
distributed_commuters = dict()
for key, value in commuter_distribution.items():
    distributed_commuters[key] = tuple([round(z * round(n / min(value))) for z in value])


class SampleCommuterProcess(Process):
    """
    Samples commuters from previously matched routes.
    """

    def __init__(self, matching_queue, counter, exit_event):
        """Initialize Commutersampleer

        :param matching_queue: Queue with work
        :type matching_queue: queue.Queue
        :param counter: Counter for sampling
        :type counter: helper.counter.Counter
        :param exit_event: Signal to exit process
        :type exit_event: multiprocessing.Event
        :return:
        """
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.mq = matching_queue
        self.exit_event = exit_event
        self.counter = counter

    def run(self):
        while True:
            '''Flow control'''
            # Get a MatchingDistribution
            try:
                work = self.mq.get(timeout=1)
            except Empty:
                continue
            finally:
                if not work or self.exit_event.is_set():
                    break

            rs, outgoing, within = work

            '''Start sampling'''
            self.logging.debug('Start matching points for: %12s', rs)
            start_time = time.time()

            with connection.get_connection() as conn:
                cur = conn.cursor()
                result = []

                '''Outgoing sampling'''
                temp_sql = 'CREATE TEMPORARY TABLE possible_commuters(i, commuter) ON COMMIT DROP AS ' \
                           'SELECT row_number() OVER () as i, r.id as commuter ' \
                           'FROM de_sim_points_start p ' \
                           '  LEFT JOIN de_sim_routes_outgoing r  ' \
                           '    ON p.id=r.start_point  ' \
                           '       AND r.distance_meter BETWEEN %(min_d)s AND %(max_d)s ' \
                           'WHERE p.rs = %(rs)s AND p.used AND r.start_point IS NOT NULL '
                sample_sql = 'INSERT INTO de_sim_routes_outgoing_sampled ' \
                             'SELECT commuter ' \
                             'FROM possible_commuters ' \
                             'WHERE i IN ( ' \
                             '  SELECT round(random() * (SELECT COUNT(i) FROM possible_commuters)) :: INTEGER AS n ' \
                             '  FROM generate_series(1, (1.2 * %(limit)s)) ' \
                             '  GROUP BY n ' \
                             ') ' \
                             'LIMIT %(limit)s'
                for i, distances in enumerate(commuting_distance):
                    args = dict(rs=rs, **distances)
                    cur.execute(temp_sql, args)
                    cur.execute('SELECT COUNT(*) FROM possible_commuters')
                    commuters, = cur.fetchone()
                    if distributed_commuters[rs[:2]][i] < commuters:
                        commuters = distributed_commuters[rs[:2]][i]
                    cur.execute(sample_sql, dict(limit=commuters))
                    try:
                        result.append((cur.rowcount / commuters))
                    except ZeroDivisionError:
                        result.append(0.0)
                    conn.commit()

                '''Within sampling'''
                sql = 'WITH possible_commuters AS ( ' \
                      '  SELECT row_number() OVER () as i, r.id as commuter ' \
                      '  FROM de_sim_points_within_start p ' \
                      '    LEFT JOIN de_sim_routes_within r  ' \
                      '      ON p.id=r.start_point  ' \
                      '  WHERE p.rs = %(rs)s AND p.used AND r.start_point IS NOT NULL ' \
                      ') ' \
                      'INSERT INTO de_sim_routes_within_sampled ' \
                      'SELECT commuter FROM possible_commuters WHERE i IN ( ' \
                      '  SELECT round(random() * (SELECT COUNT(i) FROM possible_commuters)) :: INTEGER AS n ' \
                      '  FROM generate_series(1, (1.5 * %(limit)s)) ' \
                      '  GROUP BY n ' \
                      ') ' \
                      'LIMIT %(limit)s'
                args = dict(rs=rs, limit=n)
                cur.execute(sql, args)
                result.append(cur.rowcount / n)
                conn.commit()

            count = self.counter.increment()
            self.logging.info('(%4d/%d) Finished sampling for %12s in %.2f with: %s ',
                              count, self.counter.maximum,
                              rs,
                              time.time() - start_time,
                              ', '.join(['{:.2%}'.format(x) for x in result]))
        self.logging.info('Exiting sampling process: %s', self.name)