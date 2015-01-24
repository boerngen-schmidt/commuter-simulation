import logging
import threading as t

from database import connection as db


__author__ = 'benjamin'

sql_cmd = ['TRUNCATE de_sim_routes RESTART IDENTITY CASCADE',
           'TRUNCATE de_sim_points RESTART IDENTITY CASCADE',
           'DROP INDEX IF EXISTS de_sim_points_end_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_end_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_end_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_used_idx']


def _execute_sql(sql):
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()


def run():
    logging.info('Start cleaning points.')
    threads = []
    for sql in sql_cmd:
        threads.append(t.Thread(target=_execute_sql, args=(sql, )))
        threads[-1].start()

    for thread in threads:
        thread.join()
    logging.info('Finished cleaning points.')