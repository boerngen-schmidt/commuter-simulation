from abc import ABCMeta, abstractmethod
import logging
from collections import namedtuple

from psycopg2.extras import NamedTupleCursor, RealDictCursor
from database import connection as db

FillingStation = namedtuple('FillingStation', ['id', 'target'])


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
                  '  WHERE ST_DWithin(s.geom, ST_GeomFromEWKB(%(route)s), %(distance)s); ' \
                  'UPDATE filling SET target = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
                  '  (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1); ' \
                  'SELECT target, station_id FROM filling;'

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            try:
                cur.execute(sql, dict(distance=distance_meter, route=self.env.route.geom_line))
                stations = cur.fetchall()
            except Exception:
                log = logging.getLogger('database')
                log.exception('Could not execute query. "%s"', cur.query)
                conn.rollback()
                raise
            else:
                conn.commit()
        if len(stations) == 0:
            raise NoFillingStationError('No filling station was found for commuter %s', self.env.commuter.id)
        else:
            for station in stations:
                self._refillstations.append(FillingStation(target=station.target, id=station.station_id))
        self.env.result.set_commuter_filling_stations(self.stations_ids)

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
            raise NoFillingStationError('No target filling station set. Can not calculate proxy price. Commuter %s' % self.env.commuter.id)

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
        return [s.target for s in self._refillstations]

    @property
    def stations_ids(self):
        return [s.id for s in self._refillstations]

    def station_id(self, index):
        return self._refillstations[index].id

    def station_point(self, index):
        return self._refillstations[index].target

    @abstractmethod
    def find_filling_station(self):
        pass

    def refill(self):
        """Simulates the refilling process and saves the info into the Database.

        To do so the find_filling_station method has to be executed first
        :raises: FillingStationError If no target filling station was set before
        """
        if not self._target_station:
            raise NoFillingStationError('No filling station_id was set. Can not refill. Commuter %s' % self.env.commuter.id)

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            sql = 'SELECT * FROM (VALUES ({value!r})) s(station_id) LEFT JOIN LATERAL (' \
                  '  SELECT diesel, e5, e10 FROM de_tt_priceinfo ' \
                  '  WHERE station_id = s.station_id AND received <= %(now)s LIMIT 1' \
                  ') p ON TRUE'.format(value=self._target_station)
            args = dict(now=self.env.now)
            cur.execute(sql, args)
            result = cur.fetchone()
            conn.commit()

        if result[self.env.car.fuel_type]:
            price = result[self.env.car.fuel_type]
        else:
            price = self.calculate_proxy_price(self.env.car.fuel_type)

        refill_amount = self.env.car.tank_size - self.env.car.current_filling

        # add to the result of the simulation
        self.env.result.add_refill(
            self.env.commuter.id,
            self.env.rerun,
            refill_amount,
            price,
            self.env.now,
            self._target_station,
            self.env.car.fuel_type
        )
        self.env.car.refilled()         # Car has been refilled.
        self._target_station = None     # Since the station has been used reset it.


class FillingStationNotReachableError(Exception):
    pass


class SelectFillingStationError(Exception):
    pass


class NoFillingStationError(Exception):
    pass


class NoPriceError(Exception):
    pass
