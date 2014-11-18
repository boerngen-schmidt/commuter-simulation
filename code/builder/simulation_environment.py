'''
Created on 28.09.2014

@author: Benjamin
'''
from contextlib import contextmanager
import logging
import time
import multiprocessing

from helper import database
from helper import logger
from builder.process_random_point_generator_shapely import PointCreatorProcess, Counter, Command
from builder.process_point_inserter import PointInsertingProcess
from shapely.wkb import loads
from psycopg2.extras import NamedTupleCursor


def main():
    logger.setup()

    logging.info('Start filling work queue')
    work_queue = multiprocessing.Queue()
    insert_queue = multiprocessing.JoinableQueue()

    def add_command(rec):
        """Function to be used by map() to create commands for the work_queue

        :param rec: A database record with named tuple having
                        (rs, name, geom_b, area, total_area, incomming, outgoing, within)
        """
        n = [rec.outgoing, rec.incoming, rec.within, rec.within]
        t = ['start', 'end', 'within_start', 'within_end']
        polygon = loads(bytes(rec.geom_b))
        map(lambda amount, p_type:
            work_queue.put(
                Command(rec.rs, rec.name, polygon, int(round(amount * (rec.area / rec.total_area))), p_type)),
            n, t
            )

    start = time.time()
    with database.get_connection() as con:
        cur = con.cursor(cursor_factory=NamedTupleCursor)
        sql = 'SELECT c.incoming, c.within, c.outgoing, s.rs, s.gen AS name, ST_AsEWKB(s.geom) AS geom_b, ' \
              'ST_Area(s.geom) AS area, ' \
              '(SELECT SUM(ST_Area(geom)) FROM de_shp_gemeinden WHERE rs=s.rs) AS total_area ' \
              'FROM de_commuter_gemeinden c JOIN de_shp_gemeinden s ON c.rs = s.rs'
        cur.execute(sql)
        map(add_command, cur.fetchall())

    logging.info('Finished filling work queue. Time: %s', time.time()-start)
    processes = []
    counter = Counter()
    for i in range(6):
        p = PointCreatorProcess(work_queue, insert_queue, counter)
        p.set_t(1.2)
        processes.append(p)

    with inserting_process(insert_queue):
        start = time.time()
        for p in processes:
            p.start()
        for p in processes:
            p.join()

    end = time.time()
    logging.info('Runtime: %s' % (end-start,))


@contextmanager
def inserting_process(insert_queue):
    """Generator for inserting process

    :param multiprocessing.Queue insert_queue: Queue for to be inserted Objects
    """
    inserter = PointInsertingProcess(insert_queue)
    inserter.set_batch_size(5000)
    inserter.set_insert_threads(4)
    inserter.start()
    yield
    inserter.join()

if __name__ == "__main__":
    main()