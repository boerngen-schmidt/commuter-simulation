import logging

from psycopg2.extras import NamedTupleCursor
from database import connection as db
from .base import BaseRefillStrategy, NoFillingStationError, FillingStationNotReachableError


class SimpleRefillStrategy(BaseRefillStrategy):
    """
    This refilling strategy searches for the closest refilling station, based on the cars current position. It does
    not take into account anything else than the distance to the filling station.
    """
    def __init__(self, env):
        super().__init__(env)
        try:
            self._lookup_filling_stations(1000)
        except NoFillingStationError:
            self.find_closest_station_to_route()

    def find_closest_station_to_route(self):
        sql = 'CREATE TEMP TABLE filling (target integer, station_id character varying(38)) ON COMMIT DROP; ' \
              'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations ORDER BY geom <-> ST_GeomFromEWKB(%(route)s) LIMIT 1; ' \
              'UPDATE filling SET target = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1); ' \
              'SELECT station_id, target FROM filling;'
        self._lookup_filling_stations(0, sql)

    def find_filling_station(self) -> int:
        """Finds the closest refill station to the current position.

        :return: The closest point in the routing network to the filling station
        """
        sql = 'SELECT seq, id1 as start, id2 as destination, cost as distance FROM pgr_kdijkstraCost(' \
              '\'SELECT id, source, target, km as cost FROM de_2po_4pgr, (SELECT ST_Expand(ST_Extent(geom_vertex),10000) as box FROM de_2po_vertex WHERE id = ANY(%(box)s)) as box WHERE geom_way && box.box\', ' \
              '%(start)s, %(destinations)s, false, false) AS result ORDER BY cost LIMIT 1'

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            box = []
            box += self.stations_destinations
            box.append(self.env.car.current_position)
            args = dict(
                start=self.env.car.current_position,
                destinations=self.stations_destinations,
                box=box)
            try:
                cur.execute(sql, args)
                station = cur.fetchone()
            except Exception as e:
                log = logging.getLogger('database')
                log.exception(cur.query)
                conn.rollback()
                raise NoFillingStationError(e)
            else:
                conn.commit()
            self._target_station = self.station_id(self.stations_destinations.index(station.destination))
            return station.destination


class CheapestRefillStrategy(BaseRefillStrategy):
    def __init__(self, env):
        super().__init__(env)
        try:
            self._lookup_filling_stations(1000)
        except NoFillingStationError:
            self.find_closest_stations_to_route()

    def find_closest_stations_to_route(self):
        """
        First find the closest filling station to the route, then look for filling stations within 2km radius to cover
        a city with multiple filling stations

        :raises FillingStationError: If no filling station was found
        """
        sql = 'CREATE TEMP TABLE filling (target integer, station_id character varying(38)) ON COMMIT DROP;' \
              'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations ORDER BY geom <-> ST_GEomFromEWKB(%(route)s) LIMIT 1;' \
              'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations WHERE ST_DWithin(geom, (SELECT geom FROM de_tt_stations WHERE id = (SELECT station_id FROM filling)), %(distance)s);' \
              'UPDATE filling SET target = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1);' \
              'SELECT DISTINCT station_id, target FROM filling;'
        try:
            self._lookup_filling_stations(2000, sql)
        except NoFillingStationError:
            raise NoFillingStationError(
                'Extended search for filling stations did not yield any results for commuter: %s',
                self.env.commuter.id
            )

    def find_filling_station(self):
        """
        Searches for the cheapest filling station that is reachable
        :return:
        """
        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            sql = 'SELECT * FROM  (VALUES {values!s}) s(station_id, target) LEFT JOIN LATERAL ( ' \
                  '  SELECT e5, e10, diesel, received FROM de_tt_priceinfo ' \
                  '  WHERE  station_id = s.station_id AND received <= %(received)s ' \
                  '  ORDER  BY received DESC LIMIT 1' \
                  ') p ON TRUE ' \
                  'LEFT JOIN (SELECT seq, id1 as start, id2 as target, cost as distance FROM ' \
                  '  pgr_kdijkstraCost(\'SELECT id, source, target, km as cost FROM de_2po_4pgr, (SELECT ST_Expand(ST_Extent(geom_vertex),10000) as box FROM de_2po_vertex WHERE id = ANY(%(box)s) LIMIT 1) as box WHERE geom_way && box.box\', ' \
                  '  %(start)s, %(destinations)s, false, false) AS result) as p1 USING(target)' \
                  'WHERE distance <= %(reachable)s ORDER BY e5, distance LIMIT 1'
            values = ', '.join(str(x) for x in zip(self.stations_ids, self.stations_destinations))
            box = []
            box += self.stations_destinations
            box.append(self.env.car.current_position)
            args = dict(received=self.env.now,
                        reachable=self.env.car.km_left,
                        start=self.env.car.current_position,
                        destinations=self.stations_destinations,
                        box=box)
            try:
                cur.execute(sql.format(values=values), args)
            except Exception:
                log = logging.getLogger('database')
                log.error(cur.query)
                conn.rollback()
                raise FillingStationNotReachableError('Could not reach filling station for commuter %s.', self.env.commuter.id)
            else:
                conn.commit()
            result = cur.fetchone()
            if result:
                self._target_station = result.station_id
                return result.target
            else:
                raise NoFillingStationError('No filling station found for commuter: %s, having %s stations' %
                                            (self.env.commuter.id, len(self.stations_ids)))


class PricePerformanceRatioStrategy(BaseRefillStrategy):
    def __init__(self, env):
        super().__init__(env)
        pass

    def find_filling_station(self):
        pass
