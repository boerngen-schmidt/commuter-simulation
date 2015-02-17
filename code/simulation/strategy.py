from abc import ABCMeta, abstractmethod
import logging

from psycopg2.extras import NamedTupleCursor
from database import connection as db


class BaseRefillStrategy(metaclass=ABCMeta):
    def __init__(self, env):
        """
        :param env: The environment the refill strategy is used for
        :type env: simulation.environment.SimulationEnvironment
        """
        env.refilling_strategy = self
        self.env = env
        self._refillstations = None
        self._target_station = None

    @property
    def refillstation_points(self):
        return [s[0] for s in self._refillstations]

    def station_id(self, index):
        return self._refillstations[index][1]

    @abstractmethod
    def find_filling_station(self):
        pass

    @abstractmethod
    def refill(self):
        pass


class SimpleRefillStrategy(BaseRefillStrategy):
    """
    This refillingstrategy searches for the closest refilling station, based on the cars current position. It does
    not take into account anything else than the distance to the filling station.
    """
    def __init__(self, env):
        super().__init__(env)
        self._lookup_filling_stations()

    def _lookup_filling_stations(self):
        sql = 'CREATE TEMP TABLE filling (destination integer, station_id character varying(64)) ON COMMIT DROP;' \
              'INSERT INTO filling (station_id) SELECT id FROM de_tt_stations AS s ' \
              '  WHERE ST_DWithin(s.geom::geography, ST_GEomFromEWKB(%(route)s)::geography, %(distance)s);' \
              'UPDATE filling SET destination = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '  (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1);' \
              'SELECT * FROM filling;'
        self._refillstations = []
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, dict(distance=1000, route=self.env.route.geom_line))
            for station in cur.fetchall():
                self._refillstations.append(station)
            conn.commit()

        if len(self._refillstations) is 0:
            raise FillingStationError()

    def find_filling_station(self) -> int:
        """Finds the closest refill station to the current position.

        :return: The closest point in the routing network to the filling station
        """
        sql = 'SELECT seq, id1 as start, id2 as destination, cost as distance FROM pgr_kdijkstraCost(' \
              '\'SELECT id, source, target, km as cost FROM de_2po_4pgr, (SELECT ST_Expand(ST_Extent(geom_vertex),0.1) as box FROM de_2po_vertex WHERE id = %(r_start)s OR id = %(r_dest)s LIMIT 1) as box WHERE geom_way && box.box\', ' \
              '%(start)s, %(destinations)s, false, false) AS result ORDER BY cost LIMIT 1'

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            args = dict(start=self.env.car.current_position, destinations=self.refillstation_points, r_start=self.env.route.start, r_dest=self.env.route.destination)
            try:
                cur.execute(sql, args)
            except Exception as e:
                log = logging.getLogger('sql_error')
                log.critical(e)
                log.critical(cur.mogrify(sql, args))
                raise FillingStationError
            station = cur.fetchone()
            conn.commit()
        self._target_station = self.station_id(station.seq)
        return station.destination

    def refill(self):
        """Simulates the refilling process and saves the info into the Database.

        To do so the find_filling_station method has to be executed first
        :raises: FillingStationError If no target filling station was set before
        """
        if not self._target_station:
            raise FillingStationError('No filling station_id was set')

        with db.get_connection() as conn:
            cur = conn.cursor()
            sql = 'SELECT diesel, e5, e10 FROM de_tt_priceinfo WHERE station_id = %(station_id)s AND recieved <= %(now)s LIMIT 1'
            args = dict(station_id=self._target_station, now=self.env.now)
            cur.execute(sql, args)
            result = cur.fetchone()
            if result:
                diesel, e5, e10, = result
            else:
                raise NoPriceError('No Prices where found for Query: "%s"' % cur.mogrify(sql, args))

            refill_amount = self.env.car.tank_size - self.env.car.current_filling
            cur.execute('INSERT INTO de_sim_data_refill (c_id, amount, price, time, station, type) VALUES (%s, %s, %s, %s, %s, %s)',
                (self.env.commuter.id, refill_amount, e5, self.env.now, self._target_station, 'e5'))
            conn.commit()
        self.env.car.refilled()         # Car has been refilled.
        self._target_station = None     # Since the station has been used reset it.


class FillingStationError(Exception):
    pass


class NoPriceError(Exception):
    pass