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

    work_queue = multiprocessing.Queue()
    insert_queue = multiprocessing.JoinableQueue()

    with database.get_connection() as con:
        cur = con.cursor(cursor_factory=NamedTupleCursor)

        cur.execute('SELECT rs FROM de_commuter_gemeinden')
        #cur.execute('SELECT rs FROM de_commuter_gemeinden where rs=%s', ('010010000000', ))
        gemeinden = cur.fetchall()

        for gemeinde in gemeinden:
            sql = 'SELECT c.outgoing, s.rs, s.gen AS name, ST_AsEWKB(s.geom) AS geom_b, ST_Area(s.geom) AS area ' \
                  'FROM de_commuter_gemeinden c ' \
                  'JOIN de_shp_gemeinden s ' \
                  'ON c.rs = s.rs ' \
                  'WHERE c.rs = %s'
            cur.execute(sql, (gemeinde.rs, ))

            if cur.rowcount > 1:
                records = cur.fetchall()
                cur.execute('SELECT SUM(ST_Area(geom)) as total_area FROM de_shp_gemeinden WHERE rs=\'{rs}\';'.format(rs=gemeinde.rs))
                total_area = cur.fetchone().total_area

                for rec in records:
                    n = int(round(rec.outgoing * (rec.area / total_area)))
                    polygon = loads(bytes(rec.geom_b))
                    work_queue.put(Command(rec.rs, rec.name, polygon, n, 'start'))
            else:
                rec = cur.fetchone()
                polygon = loads(bytes(rec.geom_b))
                work_queue.put(Command(rec.rs, rec.name, polygon, rec.outgoing, 'start'))


    processes = []
    counter = Counter()
    for i in range(6):
        p = PointCreatorProcess(work_queue, insert_queue, counter)
        p.set_t(1.2)
        processes.append(p)

    with inserting_process(insert_queue):
        start = time.time()
        for p in processes: p.start()
        for p in processes: p.join()

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