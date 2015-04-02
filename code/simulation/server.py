__author__ = 'benjamin'

import configparser
import logging
import signal
import threading
import time

from database import connection as db
from helper import signal as sig
from helper.file_finder import find
import zmq


def first_simulation():
    """

    :return:
    """
    sql = 'SELECT id FROM de_sim_routes r WHERE NOT EXISTS ' \
          '(SELECT 1 FROM de_sim_data_commuter c WHERE c.c_id = r.id AND NOT rerun) ' \
          'ORDER BY id LIMIT 100'

    zmq_feeder = threading.Thread(target=_zeromq_feeder, args=(sql, msg_send_socket, sig.exit_event, 500))
    zmq_feeder.start()
    start = time.time()
    logging.info('Starting first simulation run')
    zmq_feeder.join()
    logging.info('Finished first run in %.2f seconds', time.time() - start)


def rerun_simulation():
    '''
    Runs the simulation again, but this time with a different refilling strategy
    :return:
    '''
    sql = 'SELECT id FROM de_sim_routes ' \
          'WHERE id > (SELECT CASE WHEN MAX(c_id) IS NULL THEN 0 ELSE MAX(c_id) END ' \
          '            FROM de_sim_data_commuter) ' \
          'ORDER BY id'
    zmq_feeder = threading.Thread(target=_zeromq_feeder, args=(sql, msg_send_socket, sig.exit_event, 500))
    zmq_feeder.start()
    start = time.time()
    logging.info('Starting second simulation run')
    zmq_feeder.join()
    logging.info('Finished first run in %.2f seconds', time.time() - start)


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
        n = 10000
        while True:
            results = cur.fetchmany(size)
            for rec in results:
                socket.send_json(dict(c_id=rec[0], rerun=rerun))
                i += 1

            if i >= n:
                k += 1
                logging.info('Send commuter: %d', k * n)
                i -= n

            if not results:
                break

            if exit_event.is_set():
                break
        logging.info('Total send commuter: %d', k * n + i)
        cur.close()
        conn.commit()
    socket.setsockopt(zmq.LINGER, 0)


config = configparser.ConfigParser()
config.read(find('messaging.conf'))
section = 'server'
conn_str = 'tcp://{host!s}:{port!s}'
if not config.has_section(section):
    raise configparser.NoSectionError('Missing section %s' % section)

context = zmq.Context()
msg_send_socket = context.socket(zmq.PUSH)
msg_send_socket.setsockopt(zmq.SNDBUF, config.getint(section, 'push_sndbuf'))
msg_send_socket.set_hwm(config.getint(section, 'push_hwm'))
args_conn_str = dict(
    host=config.get(section, 'push_host'),
    port=config.getint(section, 'push_port')
)
msg_send_socket.bind(conn_str.format(**args_conn_str))

signal.signal(signal.SIGINT, sig.signal_handler_server)