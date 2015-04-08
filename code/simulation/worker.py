import datetime
import logging
import multiprocessing as mp
import random
import threading
import time

from simulation.car import PetrolCar, DieselCar
from simulation.commuter import Commuter
from simulation.routing.route import NoRouteError, NoRoutingPointsError
from simulation.state import CommuterState, initialize_states
from simulation.environment import SimulationEnvironment
from simulation.state_machine import StateMachine
from simulation.strategy import SimpleRefillStrategy, CheapestRefillStrategy, NoFillingStationError, NoPriceError, \
    FillingStationNotReachableError
from database import connection as db
import zmq


class CommuterSimulationZeroMQ(mp.Process):
    def __init__(self, exit_event):
        super().__init__()
        self.log = logging.getLogger()
        self._ee = exit_event

    def run(self):
        self.log.info('Starting Threads ...')
        threads = []
        for i in range(2):
            threads.append(CommuterSimulationZeroMQThread(self._ee))
            threads[-1].name = self.name + 'T%d' % i
            threads[-1].start()

        for t in threads:
            t.join()
        self.log.info('Threads for %s finished working.' % self.name)


class CommuterSimulationZeroMQThread(threading.Thread):
    def __init__(self, exit_event):
        super().__init__()
        self.exit_event = exit_event
        self.log = None
        self.context = zmq.Context()

        # Configuration
        import configparser
        from helper.file_finder import find

        config = configparser.ConfigParser()
        config.read(find('messaging.conf'))
        section = 'client'
        conn_str = 'tcp://{host!s}:{port!s}'
        if not config.has_section(section):
            raise configparser.NoSectionError('Missing section %s' % section)

        # Socket to receive commuter to simulate
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.setsockopt(zmq.RCVBUF, config.getint(section, 'pull_rcvbuf'))
        self.receiver.set_hwm(config.getint(section, 'pull_hwm'))
        self.receiver.setsockopt(zmq.LINGER, 0)
        args = dict(
            host=config.get(section, 'pull_host'),
            port=config.getint(section, 'pull_port')
        )
        self.receiver.connect(conn_str.format(**args))

        # Socket for control input
        self.controller = self.context.socket(zmq.SUB)
        self.controller.setsockopt(zmq.LINGER, 0)
        args = dict(
            host=config.get(section, 'control_host'),
            port=config.getint(section, 'control_port')
        )
        self.controller.connect(conn_str.format(**args))

        # Connect to sink
        self.sink = self.context.socket(zmq.PUSG)
        args = dict(
            host=config.get(section, 'sink_host'),
            port=config.getint(section, 'sink_port')
        )
        self.sink.connect(conn_str.format(**args))

        # Process messages from both sockets
        self.poller = zmq.Poller()
        self.poller.register(self.receiver, zmq.POLLIN)
        self.poller.register(self.controller, zmq.POLLIN)

        # Simulation parameters
        tz = datetime.timezone(datetime.timedelta(hours=1))
        self.start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
        self.end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)

    def run(self):
        self.log = logging.getLogger(self.name)
        while True:
            socks = dict(self.poller.poll(1000))

            if socks.get(self.receiver) == zmq.POLLIN:
                message = self.receiver.recv_json()
                try:
                    self.simulate(message['c_id'], message['rerun'])
                except Exception as e:
                    log = logging.getLogger('exception')
                    log.exception('Simulation of commuter %d failed.', message['c_id'])

            if self.exit_event.is_set() or socks.get(self.controller) == zmq.POLLIN:
                break
        self.context.destroy(linger=0)
        self.log.info('Exiting %s', self.name)

    def simulate(self, c_id, rerun):
        start = time.time()
        env = SimulationEnvironment(self.start_time, rerun)

        try:
            # Setup Environment (done by __init__ functions of objects)
            self.setup_environment(c_id, env, rerun)

            # Set the environment for every state
            initialize_states(env)

            sm = StateMachine(CommuterState.Start)
            while env.now < self.end_time:
                action = sm.state.run()
                sm.state = sm.state.next(action)
        except (
                FillingStationNotReachableError, NoFillingStationError, NoPriceError,
                NoRouteError, NoRoutingPointsError
                ) as e:
            logging.error(e)
            env.result.set_commuter_error(e.__class__.__name__)
        else:
            self.log.info('Finished (%d) commuter in %.2f', c_id, time.time()-start)
        finally:
            self.sink.send_json(env.result.to_json())
            del env

    def setup_environment(self, c_id, env, rerun):
        if rerun:
            from psycopg2.extras import NamedTupleCursor
            with db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                args = dict(c_id=c_id)
                cur.execute('SELECT * FROM de_sim_data_commuter WHERE c_id = %(c_id)s AND NOT rerun', args)
                result = cur.fetchone()
                conn.commit()
                if result:
                    if result.fuel_type == 'e5':
                        car = PetrolCar(c_id, env)
                    else:
                        car = DieselCar(c_id, env)
                    car._tankFilling = result.tank_filling
                    commuter = Commuter(c_id, env)
                    commuter.override_parameters(result.leaving_time)
                    CheapestRefillStrategy(env)

                # Fix commuter
                cur.execute('UPDATE de_sim_data_commuter SET leaving_time = %s WHERE c_id = %s AND rerun',
                            (result.leaving_time, c_id))
                conn.commit()
        else:
            if random.random() > 0.5:
                PetrolCar(c_id, env)
            else:
                DieselCar(c_id, env)
            Commuter(c_id, env)
            SimpleRefillStrategy(env)