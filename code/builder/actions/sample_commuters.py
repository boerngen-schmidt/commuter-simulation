import multiprocessing as mp
import logging
import signal
import time

from builder.processes.sample_commuter import SampleCommuterProcess
from database import connection
from helper import signal as sig
from helper.counter import Counter


__author__ = 'benjamin'


def sample_commuters():
    """
    Matches start and end points with a randomized order of the districts
    :return:
    """
    number_of_samplers = mp.cpu_count() - 1
    matching_queue = mp.Queue()

    logging.info('Start matching points for routes.')
    logging.info('Start filling work queue.')

    with connection.get_connection() as conn:
        cur = conn.cursor()

        '''Clear previouly sampled data'''
        cur.execute('TRUNCATE de_sim_routes_outgoing_sampled; TRUNCATE de_sim_routes_within_sampled;')

        '''Collecting distributions'''
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
        counter = Counter(cur.rowcount)

        '''Start processes'''
        start = time.time()
        processes = []
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for i in range(number_of_samplers):
            processes.append(SampleCommuterProcess(matching_queue, counter, sig.exit_event))
            processes[-1].start()
        signal.signal(signal.SIGINT, sig.signal_handler)

        '''Feed the processes the work'''
        [matching_queue.put(x) for x in cur.fetchall()]
        # Add sentinels
        for i in range(number_of_samplers):
            matching_queue.put(None)

    '''Wait for sampling processes to finish'''
    for p in processes:
        p.join()

    logging.info('Runtime commuter sampling: %s', (time.time() - start))
