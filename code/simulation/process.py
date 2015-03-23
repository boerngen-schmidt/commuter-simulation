import datetime
import logging
import multiprocessing as mp
import random
import threading
import time

from simulation.car import PetrolCar, DieselCar
from simulation.commuter import Commuter, CommuterRouteError
from simulation.state import CommuterState, initialize_states
from simulation.environment import SimulationEnvironment
from simulation.state_machine import StateMachine
from simulation.strategy import SimpleRefillStrategy, CheapestRefillStrategy, FillingStationError, NoPriceError
from database import connection as db
import zmq


class CommuterSimulationZeroMQ(mp.Process):
    def __init__(self):
        super().__init__()
        self.log = logging.getLogger(self.__class__.__name__)

    def run(self):
        self.log.info('Starting Threads ...')
        threads = []
        for i in range(5):
            threads.append(CommuterSimulationZeroMQThread())
            threads[-1].start()

        for t in threads:
            t.join()
        self.log.info('Threads finished working.')


class CommuterSimulationZeroMQThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.log = logging.getLogger(self.__class__.__name__)
        self.context = zmq.Context()

        # Socket to receive commuter to simulate
        self.reciever = self.context.socket(zmq.PULL)
        self.reciever.connect('tcp://bentoo.fritz.box:2510')

        # Socket for control input
        self.controller = self.context.socket(zmq.SUB)
        self.controller.connect("tcp://bentoo.fritz.box:2512")

        # Process messages from both sockets
        self.poller = zmq.Poller()
        self.poller.register(self.reciever, zmq.POLLIN)
        self.poller.register(self.controller, zmq.POLLIN)

    def run(self):
        while True:
            socks = dict(self.poller.poll())

            if socks.get(self.reciever) == zmq.POLLIN:
                message = self.reciever.recv_json()
                self.simulate(message['c_id'], message['rerun'])

            if socks.get(self.controller) == zmq.POLLIN:
                break
        self.log.info('Exiting %s', self.name)

    def simulate(self, c_id, rerun):
        start = time.time()
        # Generate Commuter
        tz = datetime.timezone(datetime.timedelta(hours=1))
        start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
        end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)
        env = SimulationEnvironment(start_time, rerun)

        # Set the environment for every state
        initialize_states(env)

        try:
            # Setup Environment (done by __init__ functions of objects)
            self.setup_environment(c_id, env, rerun)

            sm = StateMachine(CommuterState.Start)
            while env.now < end_time:
                action = sm.state.run()
                sm.state = sm.state.next(action)
        except FillingStationError as e:
            logging.error(e)
            logging.error('No Fillingstation found for commuter %s', c_id)
            self._insert_error(c_id, e)
        except CommuterRouteError as e:
            logging.error(e)
            self._insert_error(c_id, e)
        except NoPriceError as e:
            logging.error(e)
            self._insert_error(c_id, e)
        else:
            self.log.info('Finished (%d) commuter in %.2f', c_id, time.time()-start)

    def setup_environment(self, c_id, env, rerun):
        if rerun:
            from psycopg2.extras import NamedTupleCursor
            with db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                args = dict(c_id=c_id)
                cur.execute('SELECT * FROM de_sim_data_commuter WHERE c_id = %(c_id)s', args)
                result = cur.fetchone()
                conn.commit()
            if result:
                if result.fuel_type is 'petrol':
                    car = PetrolCar(c_id, env)
                else:
                    car = DieselCar(c_id, env)
                car._tankFilling = result.tank_filling
                commuter = Commuter(c_id, env)
                commuter.override_parameters(result.leave_time)
                CheapestRefillStrategy(env)
        else:
            if random.random() > 0.5:
                PetrolCar(c_id, env)
            else:
                DieselCar(c_id, env)
            Commuter(c_id, env)
            SimpleRefillStrategy(env)

    def _insert_error(self, commuter_id, error):
        with db.get_connection() as conn:
            cur = conn.cursor()
            args = dict(error=error.__class__.__name__, id=commuter_id)
            cur.execute('UPDATE de_sim_data_commuter SET error = %(error)s WHERE c_id = %(id)s', args)
            conn.commit()