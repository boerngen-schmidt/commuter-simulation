import logging
import multiprocessing as mp
import time
import signal

from builder.commands import PointCreationCommand
from database.process_point_inserter import PointInsertIndexingThread, PointInsertingProcess
from helper import signal as sig
from helper.counter import Counter
from builder.enums import PointType
from builder.processes.random_point_generator_shapely import PointCreatorProcess
from psycopg2.extras import NamedTupleCursor
from database import connection


__author__ = 'benjamin'


def create_points():
    logging.info('Start creation of points')
    logging.info('Start filling work queue')
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    work_queue = mp.Queue()
    insert_queue = mp.Queue()
    number_of_processes = 8

    def add_command(rec):
        """Function to be used by map() to create commands for the work_queue

        :param rec: A database record with named tuple having
                        (rs, name, geom_b, area, total_area, incomming, outgoing, within)
        """
        commuters = [rec.outgoing, rec.incoming, rec.within, rec.within]
        try:
            # polygon = loads(bytes(rec.geom_b)) TODO reomve?
            polygon = None
        except TypeError:
            logging.error('Bad record: rs: %s, name: %s values: %s', rec.rs, rec.name, commuters)
            return
        [work_queue.put(PointCreationCommand(rec.rs, rec.name, polygon, amount, p_type.value))
         for amount, p_type in zip(commuters, PointType)]

    start = time.time()
    with connection.get_connection() as con:
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
              '    THEN ST_GeomFromText(\'POLYGON EMPTY\', 4326) ' \
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
              ') sums ON (sums.rs = ck.rs) ' \
              'WHERE NOT ST_IsEmpty(ST_Difference(k.geom, geo.geom))'

        cur.execute(sql)
        con.commit()
        [add_command(rec) for rec in cur.fetchall()]
    logging.info('Finished filling work queue. Time: %s', time.time() - start)

    processes = []
    counter = Counter(work_queue.qsize())
    for i in range(number_of_processes):
        work_queue.put(None)        # Add Sentinel for each process
        p = PointCreatorProcess(work_queue, insert_queue, counter, sig.exit_event)
        p.set_t(1.75)
        processes.append(p)

    # SQL inserting process
    plans = ['PREPARE de_sim_points_start_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_start (parent_geometry, geom, geom_meter, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)), ST_Transform(ST_GeomFromWKB(ST_SetSRID($2, 4326)), 900913), $3)',

             'PREPARE de_sim_points_within_start_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_within_start (parent_geometry, geom, geom_meter, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)), ST_Transform(ST_GeomFromWKB(ST_SetSRID($2, 4326)), 900913), $3)',

             'PREPARE de_sim_points_end_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_end (parent_geometry, geom, geom_meter, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)), ST_Transform(ST_GeomFromWKB(ST_SetSRID($2, 4326)), 900913), $3)',

             'PREPARE de_sim_points_within_end_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_within_end (parent_geometry, geom, geom_meter, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)), ST_Transform(ST_GeomFromWKB(ST_SetSRID($2, 4326)), 900913), $3)']
    insert_process = PointInsertingProcess(insert_queue, plans, sig.exit_event)
    insert_process.set_batch_size(5000)
    insert_process.set_insert_threads(4)
    insert_process.start()

    start = time.time()
    for p in processes:
        p.start()
    signal.signal(signal.SIGINT, sig.signal_handler)

    for p in processes:
        p.join()
    logging.info('JOINT!')
    # Stop the inserting threads
    insert_process.stop()
    insert_process.join()

    logging.info('Creating Indexes for Tables...')
    threads = []
    for table in PointType:
        t = PointInsertIndexingThread(table.value)
        threads.append(t)
        t.start()

    with connection.get_connection as conn:
        cur = conn.cursor()
        cur.execute('CREATE INDEX de_sim_points_lookup_geom_meter_idx ON public.de_sim_points_lookup USING gist (geom_meter)')
        cur.execute('CREATE INDEX de_sim_points_lookup_type_idx ON public.de_sim_points_lookup USING btree (type COLLATE pg_catalog."default")')

    for t in threads:
        t.join()
    logging.info("Finished creating Indexes.")

    end = time.time()
    logging.info('Runtime Point Creation: %s', (end - start))
