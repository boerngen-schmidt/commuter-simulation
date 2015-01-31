import logging
from multiprocessing.pool import ThreadPool

from database import connection as db


__author__ = 'benjamin'

sql_cmd = ['TRUNCATE de_sim_routes RESTART IDENTITY CASCADE',
           'TRUNCATE de_sim_points RESTART IDENTITY CASCADE',
           'TRUNCATE de_sim_points_lookup RESTART IDENTITY',
           'DROP INDEX IF EXISTS de_sim_points_end_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_end_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_end_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_end_lookup_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_start_lookup_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_end_lookup_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_geom_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_parent_relation_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_used_idx',
           'DROP INDEX IF EXISTS de_sim_points_within_start_lookup_idx',
           'DROP INDEX IF EXISTS de_sim_points_lookup_geom_meter_idx',
           'DROP INDEX IF EXISTS de_sim_points_lookup_type_idx',
           'DROP INDEX IF EXISTS de_sim_points_lookup_rs_idx']


def run():
    logging.info('Start cleaning points.')
    with ThreadPool(processes=8) as pool:
        pool.map(db.run_commands, sql_cmd)
    logging.info('Finished cleaning points.')