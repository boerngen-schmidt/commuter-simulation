from abc import ABCMeta, abstractmethod
import logging

from psycopg2.extras import NamedTupleCursor, RealDictCursor
from database import connection as db


class BaseRefillStrategy(metaclass=ABCMeta):
    def __init__(self, env):
        """
        :param env: The environment the refill strategy is used for
        :type env: simulation.environment.SimulationEnvironment
        """
        env.refilling_strategy = self
        self.env = env
        self._refillstations = []
        self._target_station = None

    def _lookup_filling_stations(self, distance_meter, sql=None):
        """
        Searches for filling stations alongside the route
        """
        if not sql:
            sql = 'CREATE TEMP TABLE filling (target integer, station_id character varying(38)) ON COMMIT DROP; ' \
                  'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations AS s ' \
                  '  WHERE ST_DWithin(s.geom, ST_GEomFromEWKB(%(route)s), %(distance)s); ' \
                  'UPDATE filling SET target = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
                  '  (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1); ' \
                  'SELECT target, station_id FROM filling;'
        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            cur.execute(sql, dict(distance=distance_meter, route=self.env.route.geom_line))
            stations = cur.fetchall()
            if not stations:
                conn.rollback()
                raise FillingStationError('No filling station was found for commuter %s' % self.env.commuter.id)
            else:
                conn.commit()

        for station in stations:
            self._refillstations.append((station.target, station.station_id))

    def calculate_proxy_price(self, fuel_type):
        """
        Calculates a proxy price if the station selected has no price yet
        :param fuel_type: The type of fuel (e5, e10, diesel) to calculate the proxy value for
        :type fuel_type: str
        :returns: Proxy value for given fuel type
        :rtype: float
        :raises: NoPriceError
        """
        if not self._target_station:
            raise FillingStationError('No target filling station set. Can not calculate proxy price')

        sql = 'SELECT AVG(e5) AS e5, AVG(e10) AS e10, AVG(diesel) as diesel FROM ( ' \
              '  SELECT id ' \
              '  FROM de_tt_stations ' \
              '  ORDER BY geom <-> (SELECT geom ' \
              '                     FROM de_tt_stations ' \
              '                     WHERE id = %(station_id)s) ' \
              '  LIMIT 5 ' \
              '  ) s(station_id)     ' \
              'LEFT JOIN LATERAL ( ' \
              '    SELECT e5, e10, diesel, received ' \
              '    FROM   de_tt_priceinfo ' \
              '    WHERE  station_id = s.station_id ' \
              '    AND    received <= %(received)s ' \
              '    ORDER  BY received DESC ' \
              '    LIMIT  1 ' \
              '   )  p ON TRUE;'
        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            args = dict(received=self.env.now, station_id=self._target_station)
            cur.execute(sql, args)
            result = cur.fetchone()
            conn.commit()
        if result[fuel_type]:
            return result[fuel_type]
        else:
            raise NoPriceError('No proxy value found')
        
    @property
    def stations_destinations(self):
        return [s[0] for s in self._refillstations]

    @property
    def stations_ids(self):
        return [s[1] for s in self._refillstations]

    def station_id(self, index):
        return self._refillstations[index][1]

    def station_point(self, index):
        return self._refillstations[index][0]

    @abstractmethod
    def find_filling_station(self):
        pass

    def refill(self):
        """Simulates the refilling process and saves the info into the Database.

        To do so the find_filling_station method has to be executed first
        :raises: FillingStationError If no target filling station was set before
        """
        if not self._target_station:
            raise FillingStationError('No filling station_id was set')

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            sql = 'SELECT * FROM (VALUES ({value!r})) s(station_id) LEFT JOIN LATERAL (' \
                  '  SELECT diesel, e5, e10 FROM de_tt_priceinfo ' \
                  '  WHERE station_id = s.station_id AND received <= %(now)s LIMIT 1' \
                  ') p ON TRUE'.format(value=self._target_station)
            args = dict(now=self.env.now)
            cur.execute(sql, args)
            result = cur.fetchone()

            if result[self.env.car.fuel_type]:
                price = result[self.env.car.fuel_type]
            else:
                price = self.calculate_proxy_price(self.env.car.fuel_type)

            refill_amount = self.env.car.tank_size - self.env.car.current_filling
            cur.execute('INSERT INTO de_sim_data_refill '
                        '(c_id, rerun, amount, price, refueling_time, station, fuel_type) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (self.env.commuter.id, self.env.rerun, refill_amount, price, self.env.now, self._target_station, self.env.car.fuel_type))
            conn.commit()
        self.env.car.refilled()         # Car has been refilled.
        self._target_station = None     # Since the station has been used reset it.


class SimpleRefillStrategy(BaseRefillStrategy):
    """
    This refilling strategy searches for the closest refilling station, based on the cars current position. It does
    not take into account anything else than the distance to the filling station.
    """
    def __init__(self, env):
        super().__init__(env)
        try:
            self._lookup_filling_stations(1000)
        except FillingStationError:
            self.find_closest_station_to_route()

    def find_closest_station_to_route(self):
        sql = 'CREATE TEMP TABLE filling (target integer, station_id character varying(38)) ON COMMIT DROP; ' \
              'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations ORDER BY geom <-> ST_GEomFromEWKB(%(route)s) LIMIT 1; ' \
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
            args = dict(
                start=self.env.car.current_position,
                destinations=self.stations_destinations,
                box=self.stations_destinations.append(self.env.car.current_position))
            try:
                cur.execute(sql, args)
                station = cur.fetchone()
            except Exception as e:
                log = logging.getLogger('sql_error')
                log.critical(e)
                log.critical(cur.mogrify(sql, args))
                conn.rollback()
                raise FillingStationError(e)
            else:
                conn.commit()
            self._target_station = self.station_id(station.seq)
            return station.destination


class CheapestRefillStrategy(BaseRefillStrategy):
    def __init__(self, env):
        super().__init__(env)
        try:
            self._lookup_filling_stations(1000)
        except FillingStationError:
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
              'SELECT station_id, target FROM filling;'
        try:
            self._lookup_filling_stations(2000, sql)
        except FillingStationError:
            raise

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
                  '  pgr_kdijkstraCost(\'SELECT id, source, target, km as cost FROM de_2po_4pgr, (SELECT ST_Expand(ST_Extent(geom_vertex),0.1) as box FROM de_2po_vertex WHERE id = ANY(%(box)s) LIMIT 1) as box WHERE geom_way && box.box\', ' \
                  '  %(start)s, %(destinations)s, false, false) AS result) as p1 USING(target)' \
                  'WHERE distance <= %(reachable)s ORDER BY e5, distance LIMIT 1'
            values = ', '.join(str(x) for x in self._refillstations)
            args = dict(received=self.env.now,
                        reachable=self.env.car.km_left,
                        start=self.env.car.current_position,
                        destinations=self.stations_destinations,
                        box=self.stations_destinations.append(self.env.car.current_position))
            try:
                cur.execute(sql.format(values=values), args)
            except Exception as e:
                log = logging.getLogger('sql_error')
                log.critical(e)
                log.critical(cur.mogrify(sql, args))
                conn.rollback()
                raise FillingStationError
            else:
                conn.commit()
            result = cur.fetchone()
            if result:
                self._target_station = result.station_id
                return result.target
            else:
                raise FillingStationError('No filling station found for commuter: %s, having %s stations' %
                                          (self.env.commuter.id, len(self._refillstations)))


class FillingStationError(Exception):
    pass


class NoPriceError(Exception):
    pass