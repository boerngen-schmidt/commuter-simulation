import multiprocessing as mp
import logging
import signal
import time

from builder import signal_handler, exit_event
from database import connection
from helper.counter import Counter
from builder.commuter_distribution import MatchingDistribution
from builder.processes.mass_matcher import PointMassMatcherProcess


__author__ = 'benjamin'


def match_points():
    """
    Matches start and end points with a randomized order of the districts
    :return:
    """
    number_of_matchers = 8
    max_age_distribution = 3
    matching_queue = mp.Queue()

    logging.info('Start matching points for routes.')
    logging.info('Start filling work queue.')

    with connection.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT rs, outgoing, within FROM de_commuter ORDER BY RANDOM()')
        conn.commit()
        counter = Counter(cur.rowcount * max_age_distribution)
        for rec in cur.fetchall():
            obj = MatchingDistribution(rec[0], rec[1], rec[2])
            matching_queue.put(obj)

    start = time.time()
    processes = []
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    for i in range(number_of_matchers):
        processes.append(PointMassMatcherProcess(matching_queue, counter, exit_event, max_age_distribution))
        processes[-1].start()
    signal.signal(signal.SIGINT, signal_handler)

    for p in processes:
        p.join()

    end = time.time()
    logging.info('Runtime Point Matching: %s', (end - start))
