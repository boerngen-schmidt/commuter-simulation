'''
Generates Simulation Environment

@author: Benjamin
'''
from contextlib import contextmanager
import logging
import time
import multiprocessing

from builder import PointType
from builder.process_point_mass_matcher import PointMassMatcherProcess
from helper import database
from helper import logger
from builder.process_random_point_generator_shapely import PointCreatorProcess, Counter, PointCreationCommand
from builder.process_point_inserter import PointInsertingProcess, PointInsertIndexingThread
from helper.commuter_distribution import MatchingDistribution
from shapely.wkb import loads
from psycopg2.extras import NamedTupleCursor


def main():
    logger.setup()
    # create_points()
    match_points()


def create_points():
    logging.info('Start creation of points')
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
        try:
            polygon = loads(bytes(rec.geom_b))
        except TypeError:
            logging.error('Bad record: rs: %s, name: %s values: %s', rec.rs, rec.name, n)
            return
        [work_queue.put(PointCreationCommand(rec.rs, rec.name, polygon, amount, p_type)) for amount, p_type in
         zip(n, t)]

    start = time.time()
    with database.get_connection() as con:
        logging.info('Executing query for Gemeinden ...')
        cur = con.cursor(cursor_factory=NamedTupleCursor)
        sql = 'SELECT ' \
              's.rs              AS rs, ' \
              's.gen             AS name, ' \
              'c.incoming        AS incoming, ' \
              'c.within          AS within, ' \
              'c.outgoing        AS outgoing, ' \
              'ST_AsEWKB(s.geom) AS geom_b ' \
              'FROM de_commuter_gemeinden c  ' \
              'LEFT JOIN (' \
              '  SELECT rs, gen, ST_Union(geom) AS geom FROM de_shp_gemeinden ' \
              '  WHERE rs IN (SELECT rs FROM de_commuter_gemeinden) GROUP BY rs, gen) s USING (rs) '
        cur.execute(sql)
        con.commit()
        [add_command(rec) for rec in cur.fetchall()]

        logging.info('Executing query for Kreise ...')
        sql = 'SELECT  ' \
              'k.rs                                       AS rs, ' \
              'k.gen                                      AS name, ' \
              '(ck.incoming-COALESCE(sums.incoming, 0))   AS incoming,  ' \
              '(ck.outgoing-COALESCE(sums.outgoing, 0))   AS outgoing,  ' \
              '(ck.within-COALESCE(sums.within, 0))       AS within, ' \
              'ST_AsEWKB(ST_Difference(k.geom, geo.geom)) AS geom_b  ' \
              'FROM de_commuter_kreise ck   ' \
              'INNER JOIN (  ' \
              '  SELECT rs,gen,ST_Union(geom) AS geom FROM de_shp_kreise WHERE rs IN (SELECT rs FROM de_shp_kreise GROUP BY rs HAVING COUNT(rs) > 1) GROUP BY rs,gen  ' \
              '  UNION  ' \
              '  SELECT rs,gen,geom FROM de_shp_kreise WHERE rs NOT IN (SELECT rs FROM de_shp_kreise GROUP BY rs HAVING COUNT(rs) > 1)  ' \
              ') k ON (ck.rs=k.rs)  ' \
              'LEFT JOIN (  ' \
              '  SELECT DISTINCT  ' \
              '  k.rs     AS rs,  ' \
              '  CASE WHEN geo.geom IS NULL  ' \
              '    THEN ST_GeomFromText(\'POLYGON EMPTY\', 900913) ' \
              '    ELSE geo.geom ' \
              '  END AS geom ' \
              '  FROM de_shp_kreise AS k  ' \
              '  LEFT JOIN (  ' \
              '    SELECT  ' \
              '    ST_Union(g.geom) AS geom, SUBSTRING(g.rs FOR 5) AS rs  ' \
              '    FROM de_shp_gemeinden AS g  ' \
              '    INNER JOIN de_commuter_gemeinden c ON c.rs = g.rs  ' \
              '    GROUP BY SUBSTRING(g.rs FOR 5)  ' \
              '  ) geo ON (k.rs=geo.rs)  ' \
              ') geo ON (geo.rs=ck.rs)  ' \
              'LEFT OUTER JOIN (  ' \
              '  SELECT  ' \
              '  SUBSTRING(rs FOR 5) AS rs,  ' \
              '  SUM(incoming)       AS incoming,  ' \
              '  SUM(within)         AS within,  ' \
              '  SUM(outgoing)       AS outgoing  ' \
              '  FROM de_commuter_gemeinden  ' \
              '  GROUP BY SUBSTRING(rs FOR 5)  ' \
              ') sums ON (sums.rs = ck.rs) '

        cur.execute(sql)
        con.commit()
        [add_command(rec) for rec in cur.fetchall()]
    logging.info('Finished filling work queue. Time: %s', time.time() - start)

    processes = []
    counter = Counter()
    for i in range(6):
        p = PointCreatorProcess(work_queue, insert_queue, counter)
        p.set_t(1.2)
        processes.append(p)

    plans = ['PREPARE de_sim_points_start_plan (varchar, geometry) AS '
             'INSERT INTO de_sim_points_start (parent_geometry, geom) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 900913)))',

             'PREPARE de_sim_points_within_start_plan (varchar, geometry) AS '
             'INSERT INTO de_sim_points_within_start (parent_geometry, geom) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 900913)))',

             'PREPARE de_sim_points_end_plan (varchar, geometry) AS '
             'INSERT INTO de_sim_points_end (parent_geometry, geom) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 900913)))',

             'PREPARE de_sim_points_within_end_plan (varchar, geometry) AS '
             'INSERT INTO de_sim_points_within_end (parent_geometry, geom) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 900913)))']
    with inserting_process(insert_queue, plans, 4):
        start = time.time()
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        logging.info('Creating Indexes for Tables...')
        threads = []
        for table in PointType:
            t = PointInsertIndexingThread(table.value)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        logging.info("Finished creating Indexes.")

    end = time.time()
    logging.info('Runtime Point Creation: %s', (end - start))


def match_points():
    """
    Matches start and end points with a randomized order of the districts
    :return:
    """
    district_queue = multiprocessing.Queue()
    with database.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT rs FROM de_commuter ORDER BY RANDOM()')
        [district_queue.put(MatchingDistribution(rec[0])) for rec in cur.fetchall()]
    insert_queue = multiprocessing.JoinableQueue()

    processes = []
    for i in range(6):
        processes.append(PointMassMatcherProcess(district_queue, insert_queue))

    plans = ['PREPARE de_sim_routes_within_plan (integer, integer) AS '
             'INSERT INTO de_sim_routes_within (start_point, end_point) '
             'VALUES($1, $2)',

             'PREPARE de_sim_routes_outgoing_plan (integer, integer) AS '
             'INSERT INTO de_sim_routes_outgoing (start_point, end_point) '
             'VALUES($1, $2)']
    with inserting_process(insert_queue, plans, 2):
        start = time.time()
        for p in processes:
            p.start()
        for p in processes:
            p.join()

    end = time.time()
    logging.info('Runtime Point Matching: %s', (end - start))


@contextmanager
def inserting_process(insert_queue, plans, threads=2, batch_size=5000):
    """Generator for inserting process

    :param multiprocessing.Queue insert_queue: Queue for to be inserted Objects
    """
    insert_process = PointInsertingProcess(insert_queue, plans)
    insert_process.set_batch_size(batch_size)
    insert_process.set_insert_threads(threads)
    insert_process.start()
    yield
    insert_process.join()


if __name__ == "__main__":
    main()