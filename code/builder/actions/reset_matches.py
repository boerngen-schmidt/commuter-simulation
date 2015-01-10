import logging
import threading as t

from database import connection as db


__author__ = 'benjamin'

sql_cmd = ['TRUNCATE de_sim_routes RESTART IDENTITY CASCADE',
           'UPDATE de_sim_points_start SET used = false WHERE used',
           'UPDATE de_sim_points_within_start SET used = false WHERE used',
           'UPDATE de_sim_points_end SET used = false WHERE used',
           'UPDATE de_sim_points_within_end SET used = false WHERE used']


def _execute_sql(sql):
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()


def run():
    logging.info('Start resetting points and cleaning matches.')
    threads = []
    for sql in sql_cmd:
        threads.append(t.Thread(target=_execute_sql, args=(sql, )))
        threads[-1].start()

    for thread in threads:
        thread.join()
    logging.info('Finished resetting points and cleaning matches.')