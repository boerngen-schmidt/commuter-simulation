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


class PointMatcherProcess(Process):
    """
    Point Matcher class
    """
    def __init__(self):
        self.logging = logging.getLogger(self.__name__)

    def run(self):
        with database.get_connection() as conn:
            cur = conn.cursor()

    def match_within(self):
        with database.get_connection()  as conn:
            cur = conn.cursor()
            cur.execute('SELECT p.* FROM de_sim_points p, de_sim_routes r WHERE type=%s AND DOES NOT EXIST IN ROUTE TABLE', ('within_start', ))

            SELECT ST_Intersection(
ST_Difference(
  ST_Buffer(St_GeomFromText('POINT(10 10)'), 5),
  ST_Buffer(St_GeomFromText('POINT(10 10)'), 2)
),
ST_GeomFromText('POLYGON((6 6, 6 12, 12 12, 12 6, 6 6))')
)