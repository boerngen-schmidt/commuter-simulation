import time
from multiprocessing import Process
from psycopg2 import InternalError
import logging

from database import connection


class ProcessRouteCalculation(Process):
    def __init__(self, route_queue, route_counter):
        Process.__init__(self)
        self.logging = logging.getLogger(self.name)
        self.rq = route_queue
        self.counter = route_counter

    def run(self):
        i = 0
        start_time = time.time()
        while True:
            r_info = self.rq.get()

            # Sentinal to stop Process
            if isinstance(r_info, StopIteration):
                break
            else:
                (r_id, start, destination) = r_info

            with connection.get_connection() as conn:
                cur = conn.cursor()
                '''Generate route'''
                sql_route = 'INSERT INTO de_sim_routes_calculated ' \
                            'SELECT %(id)s AS points, seq, id FROM pgr_dijkstra( ' \
                            '  \'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
                            '    (SELECT ST_Expand(ST_Extent(the_geom),0.1) as box FROM de_2po_4pgr_vertices_pgr ' \
                            '      WHERE id = (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(start)s), 4326) LIMIT 1) ' \
                            '      OR id = (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(dest)s), 4326) LIMIT 1) ' \
                            '    ) as box' \
                            '    WHERE geom_way && box.box\', ' \
                            '  (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(start)s), 4326) LIMIT 1), ' \
                            '  (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(dest)s), 4326) LIMIT 1), ' \
                            '  false, ' \
                            '  false) algo, ' \
                            '  de_2po_4pgr AS r ' \
                            '  WHERE algo.id2 = r.id'
                try:
                    cur.execute(sql_route, {'id': r_id, 'start': start, 'dest': destination})
                except InternalError as err:
                    self.logging.error('Error in route calculation. Code: %s "%s"', err.pgcode, err.pgerror)
                    conn.rollback()
                else:
                    conn.commit()
                    if i >= 100:
                        self.logging.info('(%8d/%d) Generated route in %s',
                                          self.counter.increment(n=i), self.counter.maximum,
                                          time.time() - start_time)
                        i = 0
                        start_time = time.time()
                    else:
                        i += 1
        self.logging.info('Exiting Route Process: %s', self.name)
