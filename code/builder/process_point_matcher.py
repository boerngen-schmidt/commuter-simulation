"""
Class for Matching start and endpoints of a simulation

Pseudo code:
Get random start point
    if point is part of commuter within an area
        get area of startpoint
Build dount around the point (bigger buffer, substract smaller buffer
Select all points within this donut
Randomly choose one of the points
Calculate route
If does route match the wanted conditions?
    Save route and point to database
Else choose another point
"""
import logging
from multiprocessing import Process

from helper import database


class CommuterDistribution(object):
    def __init__(self):




class PointMatcherProcess(Process):
    """
    Point Matcher class
    """
    def __init__(self):
        self.logging = logging.getLogger(self.__name__)

    def run(self):
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('select * from de_sim_points WHERE point_type = %s offset random() * (select count(*) from de_sim_points WHERE point_type=%s) limit 1 ;', ('start',))
                start = cur.fetchone()

                cur.execute('select * from de_sim_points WHERE point_type = %s offset random() * (select count(*) from de_sim_points WHERE point_type=%s) limit 1 ;', ('end',))
                end = cur.fetchone()

    def fetch_start_point(self):
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM de_sim_points_start offset random() * (select count(*) from de_sim_points) limit 1 ;', ('start',))
                start = cur.fetchone()
                return start

    def fetch_end_point(self):
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROm de_sim_points_end offset random() * (select count(*) from de_sim_points WHERE point_type=%s) limit 1 ;', ('end',))
                end = cur.fetchone()
                return end

        # with database.get_connection() as conn:
        #     cur = conn.cursor()
        #     cur.execute('SELECT rs FROM de_commuter_gemeinden')
        #     gemeinden = cur.fetchall()
        #
        # while gemeinde in gemeinden:
        #     with database.get_connection() as conn:
        #

    def match_within(self):
        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT p.* FROM de_sim_points p WHERE point_type=%s AND NOT EXISTS (SELECT 1 FROM de_sim_routes r WHERE p.id == r.start_point)', ('within_start', ))

    def match(self):

WITH x AS (
    SELECT geom, parent_geometry
    FROM de_sim_points
    WHERE point_type = 'start' AND id = %s
)
SELECT p.*, St_Distance(p.geom, x.geom) as distance
FROM de_sim_points p, x
WHERE
  ST_DWithin(p.geom, x.geom, %s)
  AND p.parent_geometry != x.parent_geometry
  AND p.point_type = 'end'
  AND St_Distance(p.geom, x.geom) > %s
ORDER BY distance

Find nearest point
            SELECT * FROM de_2po_4pgr_vertices_pgr,
(SELECT ST_Transform(geom, 4326) as geom from de_sim_points WHERE point_type = 'start' offset random() * (select count(*) from de_sim_points WHERE point_type='start') limit 1) as start
ORDER BY the_geom <-> start.geom
LIMIT 1;