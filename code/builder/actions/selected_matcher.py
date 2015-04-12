import multiprocessing as mp
import logging
import signal
import time

from builder.processes.matcher_revised import PointMatcherRevised
from database import connection
from helper import signal as sig
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
        '''Collecting distributions'''
        cur = conn.cursor(cursor_factory=NamedTupleCursor)
        cur.execute('SELECT * FROM ('
                    'SELECT rs, outgoing, within FROM de_commuter_gemeinden  '
                    'UNION '
                    'SELECT rs, outgoing, within FROM de_commuter_kreise '
                    '  WHERE rs NOT IN ('
                    '   SELECT SUBSTRING(rs FOR 5) '
                    '   FROM de_commuter_gemeinden '
                    '   WHERE SUBSTRING(rs FROM 6) = \'0000000\')'
                    ') matchpoints '
                    'ORDER BY RANDOM()')
        conn.commit()
        counter = Counter(cur.rowcount * (len(cd.commuting_distance) + 1))

        '''Start processes'''
        start = time.time()
        processes = []
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for i in range(number_of_matchers):
            processes.append(PointMatcherRevised(matching_queue, counter, sig.exit_event))
            processes[-1].start()
        signal.signal(signal.SIGINT, sig.signal_handler)

        '''Feed the processes the work'''
        [matching_queue.put(x) for x in cur.fetchall()]
        # Add sentinels
        for i in range(number_of_matchers):
            matching_queue.put(None)

    for p in processes:
        p.join()

    logging.info('Runtime Point Matching: %s', (time.time() - start))
