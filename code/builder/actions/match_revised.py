import multiprocessing as mp
import logging
import signal
import time
import math

from builder.commuter_distribution import MatchingDistributionRevised
from builder.enums import MatchingType
from builder.processes.matcher_revised import PointMatcherRevised
from helper import signal as sig
from database import connection
from helper.counter import Counter
import builder.commuter_distribution as cd
from psycopg2.extras import NamedTupleCursor


__author__ = 'benjamin'


def match_points():
    """
    Matches start and end points with a randomized order of the districts
    :return:
    """
    number_of_matchers = 8
    matching_queue = mp.Queue()

    logging.info('Start matching points for routes.')
    logging.info('Start filling work queue.')

    with connection.get_connection() as conn:
        cur = conn.cursor(cursor_factory=NamedTupleCursor)
        cur.execute('SELECT rs, outgoing, within FROM de_commuter ORDER BY RANDOM()')
        conn.commit()
        counter = Counter(cur.rowcount * (len(cd.commuting_distance) +1))
        distributions = [[] for x in range(len(cd.commuting_distance))]

        start = time.time()
        processes = []
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for i in range(number_of_matchers):
            processes.append(PointMatcherRevised(matching_queue, counter, sig.exit_event))
            processes[-1].start()
        signal.signal(signal.SIGINT, sig.signal_handler)

        for rec in cur.fetchall():
            within_md = MatchingDistributionRevised(rec.rs, rec.within, MatchingType.within, 2000, -1)
            matching_queue.put(within_md)
            for i, d in enumerate(cd.commuting_distance):
                amount = int(math.floor(cd.commuter_distribution[rec.rs[:2]][i] * rec.outgoing))
                md = MatchingDistributionRevised(rec[0], amount, MatchingType.outgoing, d['min_d'], d['max_d'])
                distributions[i].append(md)

        # Add distributions to queue
        [[matching_queue.put(x) for x in mds] for mds in distributions]
        # Add sentinels
        for i in range(number_of_matchers):
            matching_queue.put(None)

    # Empty Queue if a exit event was set
    if sig.exit_event.is_set():
        while not matching_queue.empty():
            matching_queue.get()

    for p in processes:
        p.join()

    end = time.time()
    logging.info('Runtime Point Matching: %s', (end - start))
