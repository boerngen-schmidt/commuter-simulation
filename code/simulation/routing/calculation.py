import logging

from psycopg2.extras import DictCursor
from database import connection as db
from simulation import CommuterAction, RouteFragment, Route


dijkstra_sql = 'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
               '  (SELECT ST_Expand(ST_Extent(geom_vertex),0.1) as box FROM de_2po_vertex ' \
               '    WHERE id = %(start)s OR id = %(dest)s LIMIT 1 ' \
               '  ) as box WHERE geom_way && box.box'


def route_to_work(route_id):
    """Alias for calculate_route with pre set start and destination points"""
    with db.get_connection() as conn:
        sql = 'WITH info AS (SELECT end_point AS start, start_point AS dest FROM de_sim_routes WHERE id = %(id)s) ' \
              'SELECT d.id, s.id FROM ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ST_Transform(' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT start FROM info)), 4326) LIMIT 1) AS s, ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ST_Transform(' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT dest FROM info)), 4326) LIMIT 1) AS d '
        cur = conn.cursor()
        try:
            cur.execute(sql, dict(id=route_id))
        except Exception:
            logging.error(cur.query)
            raise
        start, destination = cur.fetchone()
    route = calculate_route(start, destination, CommuterAction.ArrivedAtWork)
    return route


def route_home(route_id):
    """Alias for calculate_route with pre set start and destination points"""
    with db.get_connection() as conn:
        sql = 'WITH info AS (SELECT end_point AS start, start_point AS dest FROM de_sim_routes WHERE id = %(id)s) ' \
              'SELECT s.id, d.id FROM ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ST_Transform(' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT start FROM info)), 4326) LIMIT 1) AS s, ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ST_Transform(' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT dest FROM info)), 4326) LIMIT 1) AS d '
        cur = conn.cursor()
        try:
            cur.execute(sql, dict(id=route_id))
        except Exception:
            logging.error(cur.query)
            raise
        start, destination = cur.fetchone()
    route = calculate_route(start, destination, CommuterAction.ArrivedAtHome)
    return route


def calculate_route(start, destination, action):
    """Calculates the route and returns its fragments

    Route will be calculated from the start point, which have to be part of the generated points for the simulation, to
    the given destination, also part of the generated points.

    :param int start: Id of a point in table de_2po_4pgr
    :param int destination: Id of a point in table de_2po_4pgr
    :param CommuterAction action: Action returned after driving the route
    :return: Route
    """
    with db.get_connection() as conn:
        '''Generate route'''
        sql_route = 'DROP TABLE IF EXISTS route; ' \
                    'CREATE TEMP TABLE route ON COMMIT DROP AS ' \
                    'SELECT seq, source, target, km, kmh, clazz, geom_way FROM ' \
                    '  pgr_dijkstra({dijkstra_sql!r}, %(start)s, %(dest)s, false, false) route' \
                    '  LEFT JOIN de_2po_4pgr AS info ON route.id2 = info.id'
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            args = dict(start=start, dest=destination)
            cur.execute(sql_route.format(dijkstra_sql=dijkstra_sql), args)
        except Exception:
            conn.rollback()
            raise

        cur.execute('SELECT seq, source, target, km, kmh, clazz FROM route WHERE seq < (SELECT COUNT(seq)-1 FROM route) ORDER BY seq')
        fragments = []
        for rec in cur.fetchall():
            fragments.append(
                RouteFragment(rec['seq'], rec['source'], rec['target'], rec['kmh'], rec['km'], rec['clazz']))

        cur.execute('SELECT ST_AsEWKB(ST_LineMerge(ST_union(geom_way))) FROM route')
        line, = cur.fetchone()

        cur.execute('SELECT SUM(km) FROM route')
        distance, = cur.fetchone()

        conn.commit()
    return Route(start, destination, fragments, action, line, distance)

def _save_route_info(commuter_id, route):
    with db.get_connection() as conn:
        cur = conn.cursor()
        work = (route.action is CommuterAction.ArrivedAtWork)
        for s in route:
            assert isinstance(s, RouteFragment)
            sql = 'INSERT INTO de_sim_data_routes (c_id, seq, source, destination, clazz, kmh, work) VALUES (%s, %s, %s, %s, %s, %s, %s)'
            cur.execute(sql, (commuter_id, s.seq, s.source, s.target, s.road_type, s.speed_limit, work))


