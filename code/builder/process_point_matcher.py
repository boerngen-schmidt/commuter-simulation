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
from multiprocessing import Process, Queue
from threading import Thread

from helper import database


commuter_distribution = {'01': [],
                         '02': [],
                         '03': [],
                         '04': [],
                         '05': [],
                         '06': [],
                         '07': [],
                         '08': [],
                         '09': [],
                         '10': [],
                         '11': [],
                         '12': [],
                         '13': [],
                         '14': [],
                         '15': [],
                         '16': []}


class PointMatcherProcess(Process):
    """
    Point Matcher class
    """

    def __init__(self):
        self.logging = logging.getLogger(self.__name__)
        self.point_q = Queue()
        self.matcher_threads = 3

    def run(self):
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT rs FROM de_commuter')
                rs = [rec[0] for rec in cur.fetchall()]

        while len(rs) > 0:
            current_rs = rs.pop()
            self.logging.info('Start matching for %s', current_rs)
            self.fill_queue(current_rs)
            threads = []
            for i in range(self.matcher_threads):
                name = 'Matcher Thread %s' % i
                t = PointMatcherThread(self.point_q)
                t.setName(name)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            self.logging.info('Finished matching for %s', current_rs)

    def match_within(self):
        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT p.* FROM de_sim_points p WHERE point_type=%s AND NOT EXISTS (SELECT 1 FROM de_sim_routes r WHERE p.id == r.start_point)',
                ('within_start', ))


    def fill_queue(self, rs):
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM de_sim_points_within_start WHERE parent_geometry = %s', (rs, ))
                conn.commit()
                [self.point_q.put(p[0]) for p in cur.fetchall()]


class PointMatcherThread(Thread):
    def __init__(self, q: Queue):
        """

        :param q: Queue with ID of points
        :return:
        """
        Thread.__init__(self)
        self.q = q
        self.logging = logging.getLogger(self.__name__)

    def run(self):
        while not self.q.emtpy():
            p_id = self.q.get()
            while True:
                with database.get_connection() as conn:
                    cur = conn.cursor()
                    sql = 'WITH s AS (SELECT * FROM de_sim_points_start WHERE id = %(start)s) ' \
                          'SELECT s.id AS start, e.id AS destination ' \
                          'FROM de_sim_points_end AS e, s ' \
                          'WHERE ST_DWithin(e.geom::geography, s.geom::geography, %(max_d)s) ' \
                          '  AND e.parent_geometry = s.parent_geometry ' \
                          '  AND ST_Distance(e.geom::geography, s.geom::geography) > %(min_d)s ' \
                          '  AND e.used = false ' \
                          'ORDER BY RANDOM() ' \
                          'LIMIT 1 ' \
                          'FOR UPDATE'
                    cur.execute(sql, {'start': p_id, 'max_d': 10000, 'min_d': 2000})
                    if cur.rowcount == 0:
                        self.logging.warning('No possible end point found for %s', p_id)
                    (destination, ) = cur.fetchone()
                    cur.execute('UPDATE de_sim_points_end SET used = true WHERE used = false AND id = %s',
                                (destination, ))
                    if cur.rowcount is 0:
                        # Update did not work, rollback, find new point
                        conn.rollback()
                        continue
                    cur.execute('INSERT INTO de_sim_routes (start_point, end_point) VALUES (%s, %s)',
                                (p_id, destination,))
                    conn.commit()

