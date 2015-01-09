import logging
import threading
import time

from database import connection
from helper.counter import Counter
from routing.process_route_calculation import ProcessRouteCalculation


__author__ = 'benjamin'


def generate_routes():
    logging.info('Start of route generation')
    number_of_processes = 8
    route_queue = Queue(maxsize=20000)
    sql = 'SELECT id, start_point, end_point FROM de_sim_routes'
    threading.Thread(target=_queue_feeder, args=(sql, route_queue, 20000, number_of_processes)).start()

    with connection.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(id) FROM de_sim_routes')  # execute 1.7 Secs
        rec = cur.fetchone()
        counter = Counter(rec[0])

    while not route_queue.full():
        time.sleep(0.2)

    start = time.time()
    processes = []
    for i in range(number_of_processes):
        p = ProcessRouteCalculation(route_queue, counter)
        processes.append(p)
        processes[-1].start()

    for p in processes:
        p.join()

    end = time.time()
    logging.info('Runtime Route Generation: %s', (end - start))


def _queue_feeder(sql, queue, size=5000, sentinels=8):
    while True:
        with connection.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            results = cur.fetchmany(size)
            for rec in results:
                queue.put(rec)
            if sentinels > 0 and not results:
                for i in range(sentinels):
                    queue.put(StopIteration)
                break
            elif not results:
                break