import time
from multiprocessing import Process
import logging

from helper import database


class ProcessRouteCalculation(Process):
    def __init__(self, route_queue, route_counter):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.rq = route_queue
        self.count = route_counter

    def run(self):
        while not self.rq.empty():
            start_time = time.time()
            (id, start, destination) = self.rq.get()
            with database.get_connection() as conn:
                cur = conn.cursor()
                '''Generate route'''
                sql_route = 'INSERT INTO de_sim_points_calculated ' \
                            'SELECT %(id)s AS points, seq, id FROM pgr_astar( ' \
                            '  \'SELECT id, source, target, cost, x1, y1, x2, y2 FROM de_2po_4pgr\', ' \
                            '  (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(start)s), 4326) LIMIT 1), ' \
                            '  (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(dest)s), 4326) LIMIT 1), ' \
                            '  false, ' \
                            '  false) algo, ' \
                            '  de_2po_4pgr AS r ' \
                            '  WHERE algo.id2 = r.id'
                cur.execute(sql_route, {'id': id, 'start': start, 'dest': destination})
                conn.commit()

            self.logging.info('(%8d/%d) Generated route in %s',
                              self.counter.increment(), self.counter.max,
                              time.time() - start_time)
        self.logging.info('Exiting Route Process: %s', self.name)