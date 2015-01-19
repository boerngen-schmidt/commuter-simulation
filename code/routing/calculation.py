from psycopg2.extras import NamedTupleCursor
from routing.route import RouteFragment, Route
from database import connection as db
from simulation.event import Event

dijkstra_sql = 'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
               '  (SELECT ST_Expand(ST_Extent(geom_vertex),0.1) as box FROM de_2po_vertex ' \
               '    WHERE id = %(start)s) OR id = %(dest)s LIMIT 1) ' \
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
        cur.execute(sql, {'id': route_id})
        start, destination = cur.fetchone()
    return calculate_route(start, destination, Event.ArrivedAtWork)


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
        cur.execute(sql, {'id': route_id})
        start, destination = cur.fetchone()
    return calculate_route(start, destination, Event.ArrivedAtHome)


def calculate_route(start, destination, event):
    """Calculates the route and returns its fragments

    Route will be calculated from the start point, which have to be part of the generated points for the simulation, to
    the given destination, also part of the generated points.

    :param start: Id of a point in table de_2po_4pgr
    :param destination: Id of a point in table de_2po_4pgr
    :return: Route
    """
    with db.get_connection() as conn:
        '''Generate route'''
        sql_route = 'DROP TABLE IF EXISTS route; ' \
                    'CREATE TEMP TABLE route ON COMMIT DROP AS ' \
                    'SELECT seq, source, target, km, kmh, clazz, geom_way FROM ' \
                    '  pgr_dijkstra( %(dijkstra_sql)s, %(start)s, %(dest)s), false, false) route ' \
                    '  LEFT JOIN de_2po_4pgr AS info ON route.id2 = info.id'
        cur = conn.cursor(cursor_factory=NamedTupleCursor)
        try:
            cur.execute(sql_route, dict(start=start, dest=destination, dijkstra_sql=dijkstra_sql))
        except Exception:
            conn.rollback()
            raise

        cur.execute('SELECT seq, source, target, km, kmh, clazz FROM route')
        fragments = []
        for rec in cur.fetchall():
            fragments.append(
                RouteFragment(rec['seq'], rec['source'], rec['target'], rec['kmh'], rec['km'], rec['clazz']))

        cur.execute('SELECT ST_LineMerge(ST_union(geom_way)) FROM route')
        line, = cur.fetchone()
        conn.commit()

    return Route(start, destination, fragments, event, line)