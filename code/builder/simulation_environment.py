'''
Created on 28.09.2014

@author: Benjamin
'''
import logging
import time
import multiprocessing

from helper import database
from helper import logger
from builder.process_random_point_generator_shapely import PointCreatorProcess, Counter, Command
from shapely.wkb import loads
from psycopg2.extras import NamedTupleCursor


def main():
    logger.setup()

    q = multiprocessing.Queue()

    with database.get_connection() as con:
        cur = con.cursor(cursor_factory=NamedTupleCursor)

        cur.execute('SELECT rs FROM de_commuter_gemeinden')
        gemeinden = cur.fetchall()

        for gemeinde in gemeinden:
            sql = 'SELECT c.outgoing, s.rs, s.gen AS name, ST_AsEWKB(s.geom) AS geom_b, ST_Area(s.geom) AS area ' \
                  'FROM de_commuter_gemeinden c ' \
                  'JOIN de_shp_gemeinden s ' \
                  'ON c.rs = s.rs ' \
                  'WHERE c.rs = {rs!r}'
            cur.execute(sql.format(rs=gemeinde.rs))

            if cur.rowcount > 1:
                records = cur.fetchall()
                cur.execute('SELECT SUM(ST_Area(geom)) as total_area FROM de_shp_gemeinden WHERE rs=\'{rs}\';'.format(rs=gemeinde.rs))
                total_area = cur.fetchone().total_area

                for rec in records:
                    n = int(round(rec.outgoing * (rec.area / total_area)))
                    polygon = loads(bytes(rec.geom_b))
                    q.put(Command(rec.rs, rec.name, polygon, n))
            else:
                rec = cur.fetchone()
                polygon = loads(bytes(rec.geom_b))
                q.put(Command(rec.rs, rec.name, polygon, rec.outgoing))


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