"""
The Simulation purpose is the comparison between using and not using a fuel price application.

To this purpose a simulation environment, containing of start and destination point as well as a road network and
fuel stations, was created. In this environment a commuter will be simulated driving a car from his start point to the
destination. The point in time when the car's tank will be refilled then is chosen through according to the current
strategy of the commuter, which can be either to use a fuel price application or not.

@author: Benjamin Börngen-Schmidt
"""
import logging
import multiprocessing as mp
import threading
import signal
import time

from database import connection as db
from helper import logger
from helper import signal as sig
from helper.counter import Counter
from simulation.process import CommuterSimulationProcess


def main():
    logger.setup()

    number_of_processes = 8

    # fetch all commuters
    logging.info('Filling simulation queue')
    commuter_sim_queue = mp.Queue(maxsize=10000)
    sql = 'SELECT id FROM de_sim_routes'
    threading.Thread(target=_queue_feeder, args=(sql, commuter_sim_queue, sig.exit_event, 500, number_of_processes)).start()

    logging.info('Starting Simulation')
    start_time = time.time()
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT count(*) FROM de_sim_routes')
        commuters, = cur.fetchone()
        conn.commit()
    counter = Counter(commuters)

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    processes = []
    for i in range(number_of_processes):
        processes.append(CommuterSimulationProcess(commuter_sim_queue, sig.exit_event, counter))
        processes[-1].start()

    signal.signal(signal.SIGINT, sig.signal_handler)

    for p in processes:
        p.join()

    logging.info('Simulation runtime %.2f', time.time()-start_time)


def _queue_feeder(sql, queue: mp.Queue, exit_event, size=500, sentinels=0):
    """Feeder thread for queues

    As the route is the main attribute that describes a commuter the thread will feed the routes to the queue
    one by one to be simulated by the commuter simulation object
    :return:
    """
    with db.get_connection() as conn:
        cur = conn.cursor('feeder')
        cur.execute(sql)
        while True:
            results = cur.fetchmany(size)
            for rec in results:
                queue.put(rec[0])
            if not results or exit_event.is_set():
                break
        if sentinels > 0:
            for i in range(sentinels):
                queue.put(None)
        conn.commit()

if __name__ == '__main__':
    main()