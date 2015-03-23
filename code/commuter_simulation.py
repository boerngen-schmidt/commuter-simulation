"""
The Simulation purpose is the comparison between using and not using a fuel price application.

To this purpose a simulation environment, containing of start and destination point as well as a road network and
fuel stations, was created. In this environment a commuter will be simulated driving a car from his start point to the
destination. The point in time when the car's tank will be refilled then is chosen through according to the current
strategy of the commuter, which can be either to use a fuel price application or not.

@author: Benjamin Börngen-Schmidt
"""
import argparse
import logging
import multiprocessing as mp
import threading
import signal
import time

import zmq
from database import connection as db
from helper import logger
from helper import signal as sig
from simulation.process import CommuterSimulationZeroMQ


def _zeromq_feeder(sql, socket, exit_event, size=500, rerun=False):
    """Feeder thread for queues

    As the route is the main attribute that describes a commuter the thread will feed the routes to the queue
    one by one to be simulated by the commuter simulation object
    :return:
    """
    with db.get_connection() as conn:
        cur = conn.cursor('feeder')
        cur.execute(sql)
        i = 0
        k = 0
        while True:
            results = cur.fetchmany(size)
            for rec in results:
                socket.send_json(dict(c_id=rec[0], rerun=rerun))
                i += 1
            if i >= 100000:
                k += 1
                logging.info('Send commuter: %dk', k*100)
                i -= 100000
            if not results or exit_event.is_set():
                logging.info('Send %d')
                break
        cur.close()
        conn.commit()


def worker():
    number_of_processes = mp.cpu_count()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    processes = []
    for i in range(number_of_processes):
        processes.append(CommuterSimulationZeroMQ(sig.exit_event))
        processes[-1].start()

    signal.signal(signal.SIGINT, sig.signal_handler)


def server():
    """
    The Server generates the commuters that should be simulated and makes them available to the workers over
    a ZeroMQ Push socket. The Clients can connect to the server's socket an pull the commuter.
    :return:
    """
    context = zmq.Context()
    msg_send_socket = context.socket(zmq.PUSH)
    msg_send_socket.set_hwm = 500
    msg_send_socket.setsockopt(zmq.LINGER, 0)
    msg_send_socket.bind('tcp://*:2510')

    signal.signal(signal.SIGINT, sig.signal_handler)

    # fetch all commuters
    logging.info('Filling simulation queue')

    sql = 'SELECT id FROM de_sim_routes ' \
          'WHERE id > (SELECT CASE WHEN MAX(c_id) IS NULL THEN 0 ELSE MAX(c_id) END ' \
          '            FROM de_sim_data_commuter) ' \
          'ORDER BY id'
    zmq_feeder = threading.Thread(target=_zeromq_feeder, args=(sql, msg_send_socket, sig.exit_event, 500))
    zmq_feeder.start()
    start = time.time()
    logging.info('Starting first simulation run')
    zmq_feeder.join()
    logging.info('Finished first run in %.2f seconds', start-time.time())

    sql = 'SELECT id FROM de_sim_routes ' \
          'WHERE id > (SELECT CASE WHEN MAX(c_id) IS NULL THEN 0 ELSE MAX(c_id) END ' \
          '            FROM de_sim_data_commuter) ' \
          'ORDER BY id'
    zmq_feeder = threading.Thread(target=_zeromq_feeder, args=(sql, msg_send_socket, sig.exit_event, 500))
    zmq_feeder.start()
    start = time.time()
    logging.info('Starting second simulation run')
    zmq_feeder.join()
    logging.info('Finished first run in %.2f seconds', start-time.time())


if __name__ == '__main__':
    logger.setup()
    parser = argparse.ArgumentParser(description='Options for running the simulation.')
    parser.add_argument('--mode', '-m', type=str, choices=['server', 'worker'], required=True)
    args = parser.parse_args()
    if args.mode == 'worker':
        worker()
    elif args.mode == 'server':
        server()
    else:
        raise Exception('No mode given. Exiting.')