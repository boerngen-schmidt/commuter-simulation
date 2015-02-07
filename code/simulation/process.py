import datetime
import logging
import multiprocessing as mp
import time

from simulation.car import SimpleCar
from simulation.commuter import Commuter, CommuterRouteError
from simulation.state import CommuterState, initialize_states
from simulation.environment import SimulationEnvironment
from simulation.state_machine import StateMachine
from simulation.strategy import SimpleRefillStrategy, FillingStationError, NoPriceError
from database import connection as db


class CommuterSimulationProcess(mp.Process):
    def __init__(self, commuter_queue: mp.Queue, exit_event: mp.Event, counter):
        super().__init__()
        self._q = commuter_queue
        self.exit_event = exit_event
        self.counter = counter
        self.log = logging.getLogger(self.__class__.__name__)

    def __del__(self):
        if self.exit_event.is_set():
            self.log.warn('Cleaning %d elements from Queue ... ', self._q.qsize())
            while not self._q.empty():
                self._q.get()

    def run(self):
        i = 0
        start = time.time()
        self.log.info('Starting process %s', self.name)
        while True:
            c_id = self._q.get()
            if not c_id or self.exit_event.is_set():
                break

            # Generate Commuter
            tz = datetime.timezone(datetime.timedelta(hours=1))
            start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
            end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)
            env = SimulationEnvironment(start_time)

            # Set the environment for every state
            initialize_states(env)

            try:
                # Setup Environment (done by __init__ functions of objects)
                SimpleCar(c_id, env)
                Commuter(c_id, env)
                SimpleRefillStrategy(env)
                sm = StateMachine(CommuterState.Start)
                while env.now < end_time:
                    action = sm.state.run()
                    sm.state = sm.state.next(action)
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
                if i >= 10:
                    count = self.counter.increment(10)
                    self.log.info('Finished (%s/%s) commuter in %s', count, self.counter.maximum, time.time()-start)
                    start = time.time()
                    i = 0
                else:
                    i += 1
        self.log.info('Exiting %s', self.name)

    def _insert_error(self, commuter_id, error):
        with db.get_connection() as conn:
            cur = conn.cursor()
            args = dict(error=error.__class__.__name__, id=commuter_id)
            cur.execute('UPDATE de_sim_data_commuter SET error = %(error)s WHERE c_id = %(id)s', args)
            conn.commit()