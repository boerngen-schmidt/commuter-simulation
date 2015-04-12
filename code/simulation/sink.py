import configparser
import datetime as dt
import json
import logging

import zmq

from helper.file_finder import find
from helper.signal import exit_event
import database.connection as db


c_sql = 'INSERT INTO de_sim_data_commuter (c_id, rerun, leaving_time, route_home_distance, route_work_distance, fuel_type, tank_filling, error) ' \
        'VALUES (%(c_id)s, %(rerun)s, %(leaving_time)s, %(route_home_distance)s, %(route_work_distance)s, %(fuel_type)s, %(tank_filling)s, %(error)s)'
ro_sql = 'INSERT INTO de_sim_data_routes (c_id, rerun, clazz, avg_kmh, km, work_route) ' \
         'VALUES (%(c_id)s, %(rerun)s, %(clazz)s, %(avg_kmh)s, %(km)s, %(work_route)s)'
re_sql = 'INSERT INTO de_sim_data_refill (c_id, rerun, amount, price, refueling_time, station, fuel_type) ' \
         'VALUES (%(c_id)s, %(rerun)s, %(amount)s, %(price)s, %(refueling_time)s, %(station)s, %(fuel_type)s)'
log = logging.getLogger('SINK')


def sink():
    config = configparser.ConfigParser()
    config.read(find('messaging.conf'))
    section = 'server'
    conn_str = 'tcp://{host!s}:{port!s}'
    if not config.has_section(section):
        raise configparser.NoSectionError('Missing section %s' % section)

    context = zmq.Context()

    sink = context.socket(zmq.PULL)
    args_conn_str = dict(
        host=config.get(section, 'sink_host'),
        port=config.getint(section, 'sink_port')
    )
    sink.bind(conn_str.format(**args_conn_str))

    poller = zmq.Poller()
    poller.register(sink, zmq.POLLIN)

    n = 100
    k = 0
    i = 0
    data = []
    while True:
        # fetch data from socket
        socks = dict(poller.poll(1000))
        if socks.get(sink) == zmq.POLLIN:
            data.append(sink.recv_json())  # possible memory killer if inserting into db does not work
            i += 1
            if i >= n:
                k += 1
                insert_data(data)
                log.info('Inserted commuters: %d', k*n)
                i = 0
                data = []

        if exit_event.is_set():
            break
    insert_data(data)
    log.info('Inserted commuters: %d' % k*n+i)


def insert_data(data):
    with db.get_connection() as conn:
        cur = conn.cursor()
        for d in data:
            d = json.loads(d)
            # First the commuter
            d['commuter']['leaving_time'] = \
                dt.datetime.strptime(d['commuter']['leaving_time'], '%H:%M:%S') \
                - dt.datetime.strptime('0:00:00', '%H:%M:%S')
            cur.execute(c_sql, d['commuter'])

            # Then the route
            for ro_data in d['route']:
                cur.execute(ro_sql, ro_data)

            # and last the refill events
            for re_data in d['refill']:
                re_data['refueling_time'] = dt.datetime.strptime(re_data['refueling_time'], '%Y-%m-%d %H:%M:%S%z')
                cur.execute(re_sql, re_data)
        conn.commit()