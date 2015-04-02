import logging

from psycopg2.extras import DictCursor
from database import connection as db
from simulation import CommuterAction, RouteFragment, Route
from simulation.routing.route import NoRouteError, NoRoutingPointsError

log = logging.getLogger('routing')
sql_log = logging.getLogger('sql_error')

dijkstra_sql = 'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
               '  (SELECT ST_Expand(ST_Extent(geom_vertex),10000) as box FROM de_2po_vertex ' \
               '    WHERE id = %(start)s OR id = %(dest)s ' \
               '  ) as box WHERE geom_way && box.box'


def route_to_work(route_id):
    """Alias for calculate_route with pre set start and destination points"""
    with db.get_connection() as conn:
        sql = '  WITH info AS (SELECT end_point AS start, start_point AS dest FROM de_sim_routes WHERE id = %(id)s) ' \
              'SELECT d.id, s.id FROM ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT start FROM info)) LIMIT 1) AS s, ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT dest FROM info)) LIMIT 1) AS d '
        cur = conn.cursor()
        try:
            cur.execute(sql, dict(id=route_id))
        except Exception:
            sql_log.exception(cur.query)
            conn.rollback()
            raise NoRoutingPointsError
        start, destination = cur.fetchone()
    route = calculate_route(start, destination, CommuterAction.ArrivedAtWork)
    _save_route_info(route_id, route)
    return route


def route_home(route_id):
    """Alias for calculate_route with pre set start and destination points"""
    with db.get_connection() as conn:
        sql = 'WITH info AS (SELECT end_point AS start, start_point AS dest FROM de_sim_routes WHERE id = %(id)s) ' \
              'SELECT s.id, d.id FROM ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT start FROM info)) LIMIT 1) AS s, ' \
              ' (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '   (SELECT geom FROM de_sim_points WHERE id = (SELECT dest FROM info)) LIMIT 1) AS d '
        cur = conn.cursor()
        try:
            cur.execute(sql, dict(id=route_id))
        except Exception:
            sql_log.exception(cur.query)
            conn.rollback()
            raise NoRoutingPointsError
        start, destination = cur.fetchone()
    route = calculate_route(start, destination, CommuterAction.ArrivedAtHome)
    _save_route_info(route_id, route)
    return route


def calculate_route(start, destination, action):
    """Calculates the route and returns its fragments

    Route will be calculated from the start point, which have to be part of the generated points for the simulation, to
    the given destination, also part of the generated points.

    :param int start: Id of a point in table de_2po_4pgr
    :param int destination: Id of a point in table de_2po_4pgr
    :param simulation.state.CommuterAction action: Action returned after driving the route
    :return: simulation.routing.route.Route
    """
    with db.get_connection() as conn:
        '''Generate route'''
        sql_route = 'CREATE TEMP TABLE route ON COMMIT DROP AS ' \
                    'SELECT seq, source, target, km, kmh, clazz, geom_way FROM ' \
                    '  pgr_dijkstra({dijkstra_sql!r}, %(start)s, %(dest)s, false, false) route' \
                    '  LEFT JOIN de_2po_4pgr AS info ON route.id2 = info.id'
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            args = dict(start=start, dest=destination)
            cur.execute(sql_route.format(dijkstra_sql=dijkstra_sql), args)
        except Exception:
            sql_log.exception(cur.query)
            conn.rollback()
            raise NoRouteError

        cur.execute('SELECT seq, source, target, km, kmh, clazz '
                    'FROM route '
                    'WHERE source IS NOT NULL ORDER BY seq')
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
        km = dict()
        kmh = dict()
        for s in route:
            assert isinstance(s, RouteFragment)
            if s.road_type in km:
                km[s.road_type].append(s.length)
            else:
                km[s.road_type] = [s.length]

            if s.road_type in kmh:
                kmh[s.road_type].append(s.speed_limit)
            else:
                kmh[s.road_type] = [s.speed_limit]

        for key in km.keys():
            sql = 'INSERT INTO de_sim_data_routes (c_id, clazz, avg_kmh, km, work_route) VALUES (%s, %s, %s, %s, %s)'
            cur.execute(sql, (commuter_id, key.value, sum(kmh[key])/len(kmh[key]), sum(km[key]), work))
            conn.commit()