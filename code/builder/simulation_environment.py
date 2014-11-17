'''
Created on 28.09.2014

@author: Benjamin
'''
import logging
import time
import multiprocessing

from helper import database
from helper import logger
from builder.process_random_point_generator_shapely import PointCreatorProcess, Counter


def main():
    logger.setup()

    gemeinden = None
    q = multiprocessing.Queue()

    # Fill the queue
    with database.get_connection() as conn:
        cur = conn.cursor()
        ''':type cur: cursor'''
        cur.execute('SELECT rs FROM de_commuter_gemeinden')

        gemeinden = cur.fetchall()
        for record in gemeinden:
            q.put(record[0])

    processes = []
    counter = Counter()
    for i in range(6):
        p = PointCreatorProcess(q, counter, False)
        p.set_t(1.2)
        processes.append(p)

    start = time.time()
    for p in processes: p.start()
    for p in processes: p.join()
    end = time.time()

    logging.info('Runtime: %s' % (end-start,))


if __name__ == "__main__":
    main()