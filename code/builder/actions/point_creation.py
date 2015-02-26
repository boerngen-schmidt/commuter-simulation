import logging
import multiprocessing as mp
import concurrent.futures
import time
import signal

from builder.commands import PointCreationCommand
from database.process_point_inserter import PointInsertingProcess
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
    number_of_processes = 7

    def add_command(rec):
        """Function to be used by map() to create commands for the work_queue

        :param rec: A database record with named tuple having
                        (rs, name, geom_b, area, total_area, incomming, outgoing, within)
        """
        commuters = [rec.outgoing, rec.incoming, rec.within, rec.within]
        [work_queue.put(PointCreationCommand(rec.rs, rec.name, amount, p_type.value))
         for amount, p_type in zip(commuters, PointType)]

    start = time.time()
    with connection.get_connection() as con:
        logging.info('Executing query for Gemeinden ...')
        cur = con.cursor(cursor_factory=NamedTupleCursor)
        sql = 'SELECT c.rs AS rs, s.gen AS name, c.incoming AS incoming, c.within AS within, c.outgoing AS outgoing ' \
              'FROM de_commuter_gemeinden c ' \
              'LEFT JOIN LATERAL (SELECT gen FROM de_shp_gemeinden WHERE rs = c.rs LIMIT 1) s ON TRUE'
        cur.execute(sql)
        con.commit()
        [add_command(rec) for rec in cur.fetchall()]

        logging.info('Executing query for Kreise ...')
        sql = 'SELECT ck.rs AS rs, k.gen AS name, ' \
              '(ck.incoming-COALESCE(sums.incoming, 0)) AS incoming, ' \
              '(ck.outgoing-COALESCE(sums.outgoing, 0)) AS outgoing, ' \
              '(ck.within-COALESCE(sums.within, 0))     AS within ' \
              'FROM de_commuter_kreise ck ' \
              'LEFT JOIN LATERAL (' \
              '  SELECT gen FROM de_shp_kreise WHERE rs = ck.rs LIMIT 1' \
              ') k ON TRUE ' \
              'LEFT JOIN LATERAL (' \
              '  SELECT ' \
              '    SUBSTRING(rs FOR 5) AS rs, ' \
              '    SUM(incoming) AS incoming, ' \
              '    SUM(within)   AS within, ' \
              '    SUM(outgoing) AS outgoing ' \
              '  FROM de_commuter_gemeinden ' \
              '  WHERE SUBSTRING(rs FOR 5) = ck.rs ' \
              '  GROUP BY SUBSTRING(rs FOR 5)' \
              ') sums ON TRUE ' \
              'WHERE (ck.incoming-COALESCE(sums.incoming, 0)) > 0 ' \
              '  AND (ck.outgoing-COALESCE(sums.outgoing, 0)) > 0 ' \
              '  AND (ck.within-COALESCE(sums.within, 0)) > 0'

        cur.execute(sql)
        con.commit()
        [add_command(rec) for rec in cur.fetchall()]
    logging.info('Finished filling work queue. Time: %s', time.time() - start)

    processes = []
    counter = Counter(work_queue.qsize())
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    for i in range(number_of_processes):
        work_queue.put(None)  # Add Sentinel for each process
        p = PointCreatorProcess(work_queue, insert_queue, counter, sig.exit_event)
        p.set_t(1.75)
        processes.append(p)

    # SQL inserting process
    plans = ['PREPARE de_sim_points_start_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_start (rs, geom, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 25832)), $3)',

             'PREPARE de_sim_points_within_start_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_within_start (rs, geom, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 25832)), $3)',

             'PREPARE de_sim_points_end_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_end (rs, geom, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 25832)), $3)',

             'PREPARE de_sim_points_within_end_plan (varchar, geometry, integer) AS '
             'INSERT INTO de_sim_points_within_end (rs, geom, lookup) '
             'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 25832)), $3)']
    insert_process = PointInsertingProcess(insert_queue, plans, sig.exit_event)
    insert_process.set_batch_size(5000)
    insert_process.set_insert_threads(1)
    insert_process.start()

    start = time.time()
    for p in processes:
        p.start()
    signal.signal(signal.SIGINT, sig.signal_handler)

    for p in processes:
        p.join()
    sig.exit_event.set()
    insert_process.join()
    logging.info('JOINT!')

    logging.info('Creating Indexes for Tables...')
    args = [(_create_index_points, p.value) for p in PointType]
    sqls = ('CREATE INDEX de_sim_points_lookup_geom_idx ON de_sim_points_lookup USING GIST (geom); '
            '  CLUSTER de_sim_points_lookup USING de_sim_points_lookup_geom_idx',
            'CREATE INDEX de_sim_points_lookup_rs_idx ON de_sim_points_lookup USING BTREE (rs)',
            'CREATE INDEX de_sim_points_lookup_point_type_idx ON de_sim_points_lookup USING BTREE (point_type)')
    args += [(connection.run_commands, s) for s in sqls]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        result = [executor.submit(a[0], a[1]) for a in args]
    result = concurrent.futures.wait(result)
    if len(result.not_done) is not 0:
        for f in result.not_done:
            logging.error(f.exception())
    logging.info("Finished creating Indexes.")

    end = time.time()
    logging.info('Runtime Point Creation: %s', (end - start))


def _create_index_points(table):
    logging.info('Start creating Indexes for de_sim_points_%s tables', table)
    with connection.get_connection() as conn:
        cur = conn.cursor()
        start_index = time.time()
        sql = 'ALTER TABLE de_sim_points_{tbl!s} SET (FILLFACTOR=80); '
        if table in ('end', 'within_end'):
            sql += 'CREATE INDEX de_sim_points_{tbl!s}_rs_geom_idx ON de_sim_points_{tbl!s} ' \
                   '  USING gist (rs COLLATE pg_catalog."default", geom) WHERE NOT used;'
        else:
            sql = 'CREATE INDEX de_sim_points_{tbl!s}_geom_idx ON de_sim_points_{tbl!s} USING GIST(geom);' \
                  'CREATE INDEX de_sim_points_{tbl!s}_rs_used_idx ON de_sim_points_{tbl!s} ' \
                  '  USING BTREE (rs COLLATE pg_catalog."default", used DESC);'
        cur.execute(sql.format(tbl=table))
        conn.commit()
        conn.set_isolation_level(0)
        cur.execute('VACUUM ANALYSE de_sim_points_{tbl!s}'.format(tbl=table))
        conn.commit()
        finish_index = time.time()
        logging.info('Finished creating indexes on de_sim_points_%s in %.2f', table, (finish_index - start_index))

