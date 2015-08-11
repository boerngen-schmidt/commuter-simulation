import datetime
import logging
import multiprocessing as mp
import threading
import time

import zmq
import simulation.fsm as fsm
from simulation.fsm import UnknownTransitionCondition
import simulation.fsm.states as s
import simulation.fsm.transitions as t
from simulation.routing import NoRouteError, NoRoutingPointsError
from simulation.environment import SimulationEnvironment
from simulation.strategy import FillingStationNotReachableError, NoFillingStationError, NoPriceError


class CommuterSimulationZeroMQ(mp.Process):
    def __init__(self, exit_event):
        """

        :param exit_event: Event to terminate the Process
        :type exit_event: threading.Event
        :return:
        """
        super().__init__()
        self.log = logging.getLogger()
        self._exit_event = exit_event

    def run(self):
        self.log.info('Starting Threads ...')
        num_threads = 1
        threads = []
        for i in range(num_threads):
            threads.append(CommuterSimulationThread(self.name + 'T%d' % i, self._exit_event))
            threads[-1].start()

        for t in threads:
            t.join()

        self.log.info('Threads for %s finished working.' % self.name)


class CommuterSimulationThread(threading.Thread):
    def __init__(self, name, exit_event):
        """

        :param name: The name of the Thread
        :type name: str
        :param queue: Work queue
        :type queue: queue.Queue
        """
        super().__init__()
        self.name = name
        self._exit_event = exit_event
        self.log = logging.getLogger(self.name)
        self.fsm = None
        """:type fsm: simulation.fsm.core.SimulationFSM"""

        # Initialize ZMQ
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
        self.sink = self.context.socket(zmq.PUSH)
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

    def _initialize_fsm(self):
        # Simulation Finite State Machine
        self.fsm = fsm.SimulationFSM()

        self.fsm.add_state(fsm.States.Start, s.Start(self.fsm))
        self.fsm.add_state(fsm.States.End, s.End(self.fsm))
        self.fsm.add_state(fsm.States.Home, s.Home(self.fsm))
        self.fsm.add_state(fsm.States.Work, s.Work(self.fsm))
        self.fsm.add_state(fsm.States.FillingStation, s.FillingStation(self.fsm))
        self.fsm.add_state(fsm.States.SearchFillingStation, s.SearchFillingStation(self.fsm))
        self.fsm.add_state(fsm.States.Drive, s.Drive(self.fsm))

        self.fsm.add_transition(
            fsm.Transitions.Start,
            t.Start(fsm.States.Start))
        self.fsm.add_transition(
            fsm.Transitions.End,
            t.End(fsm.States.End))
        self.fsm.add_transition(
            fsm.Transitions.ArriveAtFillingStation,
            t.ArriveAtFillingStation(fsm.States.FillingStation))
        self.fsm.add_transition(
            fsm.Transitions.ArriveAtHome,
            t.ArriveAtHome(fsm.States.Home))
        self.fsm.add_transition(
            fsm.Transitions.ArriveAtWork,
            t.ArriveAtWork(fsm.States.Work))
        self.fsm.add_transition(
            fsm.Transitions.DriveToFillingStation,
            t.DriveToFillingStation(fsm.States.Drive))
        self.fsm.add_transition(
            fsm.Transitions.DriveToHome,
            t.DriveToHome(fsm.States.Drive))
        self.fsm.add_transition(
            fsm.Transitions.DriveToWork,
            t.DriveToWork(fsm.States.Drive))
        self.fsm.add_transition(
            fsm.Transitions.SearchFillingStation,
            t.SearchFillingStation(fsm.States.SearchFillingStation))

    def run(self):
        while True:
            socks = dict(self.poller.poll(1000))

            if socks.get(self.receiver) == zmq.POLLIN:
                message = self.receiver.recv_json()
                try:
                    self.simulate(message['c_id'], message['rerun'])
                except Exception:
                    log = logging.getLogger('exception')
                    log.exception('Simulation of commuter %d failed.', message['c_id'])

            if self._exit_event.is_set():
                break

        # Destroy ZMQ Context and do not linger messages
        self.context.destroy(linger=0)
        self.log.info('Exiting %s', self.name)

    def simulate(self, c_id, rerun):
        start = time.time()
        self._initialize_fsm()
        env = SimulationEnvironment(self.start_time, c_id, rerun)

        try:
            # Setup FSM
            self.fsm.env = env
            self.fsm.set_transition(fsm.Transitions.Start)

            # Execute FSM
            while env.now < self.end_time:
                self.fsm.execute()

            # Manual transition to End state
            self.fsm.set_transition(fsm.Transitions.End)
            self.fsm.execute()
            
        except (
                FillingStationNotReachableError, NoFillingStationError, NoPriceError,
                NoRouteError, NoRoutingPointsError, UnknownTransitionCondition
                ) as e:
            logging.error(e)
            env.result.set_commuter_error(e.__class__.__name__)
            raise e
        except Exception as e:
            logging.error(e)
            log = logging.getLogger('exceptions')
            log.exception('Something went wrong.')
            env.result.set_commuter_error('Exception')
        else:
            self.log.info('Finished (%d) commuter in %.2f', c_id, time.time()-start)
            self.sink.send_json(env.result.to_json())
