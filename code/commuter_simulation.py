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

from database import connection as db
from helper import logger
from simulation.process import CommuterSimulationProcess


exit_event = mp.Event()
default_handler = signal.getsignal(signal.SIGINT)


def signal_handler(signum, frame):
    '''
    Signal Handler for CTRL + C (SIGINT)

    Sets an exit event, which is passed to the processes, to true.
    :param signum: Number of the signal
    :param frame: Python frame
    '''
    logging.info('Received SIGINT. Exiting processes')
    exit_event.set()
    # Reset to default handler to be able to kill force killing of process
    signal.signal(signal.SIGINT, default_handler)


def main():
    logger.setup()

    number_of_processes = 8

    # fetch all commuters
    commuter_sim_queue = mp.Queue(maxsize=10000)
    sql = 'SELECT id FROM de_sim_routes'
    threading.Thread(target=_queue_feeder, args=(sql, commuter_sim_queue, 500, number_of_processes)).start()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    processes = []
    for i in range(number_of_processes):
        processes.append(CommuterSimulationProcess(commuter_sim_queue))
        processes[-1].start()

    signal.signal(signal.SIGINT, signal_handler)

    for p in processes:
        p.join()


def _queue_feeder(sql, queue: mp.Queue, size=500, sentinels=0):
    """Feeder thread for queues

    As the route is the main attribute that describes a commuter the thread will feed the routes to the queue
    one by one to be simulated by the commuter simulation object
    :return:
    """
    with db.get_connection() as conn:
        while True:
            cur = conn.cursor()
            cur.execute(sql)
            results = cur.fetchmany(size)
            for rec in results:
                queue.put(rec[0])
            if sentinels > 0 and not results:
                for i in range(sentinels):
                    queue.put(StopIteration)
                break
            elif not results:
                break


if __name__ == '__main__':
    main()