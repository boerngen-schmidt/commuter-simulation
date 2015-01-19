from abc import ABCMeta, abstractmethod

from routing.route import Route
import routing.calculation as rc


__author__ = 'benjamin'


class BaseRefillStrategy(metaclass=ABCMeta):
    @abstractmethod
    def find_filling_station(self, data) -> Route:
        pass


class SimpleRefillStrategy(BaseRefillStrategy):
    def find_filling_station(self, data) -> Route:
        'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
        '  (SELECT ST_Expand(ST_Extent(the_geom),0.1) as box FROM de_2po_4pgr_vertices_pgr ' \
        '    WHERE id = (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(start)s), 4326) LIMIT 1) ' \
        '    OR id = (SELECT id::integer FROM de_2po_4pgr_vertices_pgr ORDER BY the_geom <-> ST_Transform((SELECT geom FROM de_sim_points WHERE id =%(dest)s), 4326) LIMIT 1) ' \
        '  ) as box WHERE geom_way && box.box'

        sql = 'SELECT info.geom_way FROM pgr_dijkstra( %(dijkstra_sql)s, %(start)s, %(dest)s, FALSE, FALSE) AS route ' \
              'LEFT JOIN de_2po_4pgr AS info ON route.id2 == info.id'
        rc.calculate_route(data['current_position'])

