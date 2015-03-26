import logging
import concurrent.futures

from database import connection as db


sql_cmds = ['TRUNCATE de_sim_routes RESTART IDENTITY CASCADE',
            'TRUNCATE de_sim_data_matching_info RESTART IDENTITY CASCADE',
            'UPDATE de_sim_points_start SET used = FALSE WHERE used',
            'UPDATE de_sim_points_within_start SET used = FALSE WHERE used',
            'UPDATE de_sim_points_end SET used = FALSE WHERE used',
            'UPDATE de_sim_points_within_end SET used = FALSE WHERE used']


def _execute_sql(sql):
    import time

    logging.info('Starting SQL command: "%s"', sql)
    start = time.time()
    db.run_commands(sql)
    logging.info('Finished SQL command: "%s" in %.2f', sql, time.time() - start)


def run():
    logging.info('Start resetting points and cleaning matches.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        result = [executor.submit(_execute_sql, sql) for sql in sql_cmds]
    result = concurrent.futures.wait(result)
    if len(result.not_done) is not 0:
        for f in result.not_done:
            logging.error(f.exception())
    logging.info('Finished resetting points and cleaning matches.')