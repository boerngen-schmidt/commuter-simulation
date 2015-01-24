from abc import ABCMeta, abstractmethod

from psycopg2.extras import NamedTupleCursor
from simulation.routing.route import Route
from simulation import routing as rc
from simulation.commuter import CommuterError
from simulation.environment import SimulationEnvironment
from database import connection as db
from simulation.event import Event


__author__ = 'benjamin'


class BaseRefillStrategy(metaclass=ABCMeta):
    def __init__(self, env: SimulationEnvironment):
        env.refilling_strategy = self
        self.env = env

    @abstractmethod
    def find_filling_station(self, data) -> (Route, str):
        pass

    @abstractmethod
    def refill(self, station_id):
        pass


class SimpleRefillStrategy(BaseRefillStrategy):
    def __init__(self, env: SimulationEnvironment):
        BaseRefillStrategy.__init__(self, env)

    def find_filling_station(self, data) -> (Route, str):
        """

        :param data: data from the simulation.event.SimEvent()
        :return:
        """
        #SQL creates a temporary table in which the stations alongside the route are selected
        sql = 'CREATE TEMP TABLE filling (start integer, destination integer, station_id character varying(255), ' \
              '  distance double precision) ON COMMIT DROP;' \
              'INSERT INTO filling (start, station_id) ' \
              '  SELECT %(start)s, id FROM de_tt_stations AS s ' \
              '  WHERE ST_DWithin(s.geom::geography, ST_GEomFromEWKB(%(route)s), 1000);' \
              'UPDATE filling SET destination = (SELECT id::integer FROM de_2po_vertex ORDER BY geom_vertex <-> ' \
              '  (SELECT geom FROM de_tt_stations WHERE id = filling.station_id) LIMIT 1);' \
              'UPDATE filling SET distance = (SELECT SUM(km) AS distance FROM ( ' \
              '	 SELECT km FROM pgr_dijkstra(' \
              '   \'SELECT id, source, target, cost FROM de_2po_4pgr, ' \
              '    (SELECT ST_Expand(ST_Extent(geom_vertex),0.05) as box FROM de_2po_vertex  ' \
              '		  WHERE id = \'|| filling.start ||\' OR id = \'|| filling.destination ||\' LIMIT 1) as box ' \
              '     WHERE geom_way && box.box\', filling.start, filling.destination, FALSE, FALSE) AS route ' \
              '	 LEFT JOIN de_2po_4pgr AS info ON route.id2 = info.id) as dist); ' \
              'SELECT * FROM filling ORDER BY distance LIMIT 1;'

        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            cur.execute(sql, dict(start=data['current_position'], route=self.env.route.geom_line))
            station = cur.fetchone()
            conn.commit()

        if not station:
            raise FillingStationError('No Fillingstation found on route')

        return rc.calculate_route(station.start, station.destination, Event.FillingStation), station.station_id

    def refill(self, station_id):
        with db.get_connection() as conn:
            cur = conn.cursor()
            sql = 'SELECT diesel, e5, e10 FROM de_tt_priceinfo WHERE station_id = %(station_id)s AND recieved <= %(now)s LIMIT 1'
            args = dict(station_id=station_id, now=self.env.now)
            cur.execute(sql, args)
            result = cur.fetchone()
            if result:
                diesel, e5, e10, = result
            else:
                raise NoPriceError('No Prices where found for Query: "%s"' % cur.mogrify(sql, args))

            refill_amount = self.env.car.tank_size - self.env.car.current_filling
            cur.execute('INSERT INTO de_sim_data_refill (c_id, amount, price, time, station, type) VALUES (%s, %s, %s, %s, %s, %s)',
                (self.env.commuter.id, refill_amount, e5, self.env.now, station_id, 'e5'))
            self.env.car.refilled()
            conn.commit()


class FillingStationError(CommuterError):
    pass


class NoPriceError(CommuterError):
    pass