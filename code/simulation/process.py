import datetime
import logging
import multiprocessing as mp
import time

from simulation.cars.car import SimpleCar
from simulation.commuter import Commuter, CommuterRouteError
from simulation.environment import SimulationEnvironment
from simulation.strategy import SimpleRefillStrategy, FillingStationError, NoPriceError
from database import connection as db


class CommuterSimulationProcess(mp.Process):
    def __init__(self, commuter_queue: mp.Queue):
        super().__init__()
        self._q = commuter_queue

    def run(self):
        while True:
            c_id = self._q.get()
            if not c_id:
                break

            # Generate Commuter
            tz = datetime.timezone(datetime.timedelta(hours=1))
            start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
            end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)
            env = SimulationEnvironment(start_time)

            start = time.time()
            try:
                # Setup Environment (done by __init__ functions)
                SimpleCar(c_id, env)
                Commuter(c_id, env)
                SimpleRefillStrategy(env)
                env.run(end_time)
            except FillingStationError as e:
                logging.error('No Fillingstation found for commuter %s', c_id)
                self._insert_error(c_id, e)
            except CommuterRouteError as e:
                logging.error(e)
                self._insert_error(c_id, e)
            except NoPriceError as e:
                logging.error(e)
                self._insert_error(c_id, e)
            else:
                logging.info('Finished commuter %s in %s', c_id, time.time()-start)

    def _insert_error(self, commuter_id, error):
        with db.get_connection() as conn:
            cur = conn.cursor()
            args = dict(error=error.__class__.__name__, id=commuter_id)
            cur.execute('UPDATE de_sim_data_commuter SET error = %(error)s WHERE c_id = %(id)s', args)
            conn.commit()