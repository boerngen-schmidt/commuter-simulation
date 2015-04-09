from abc import ABCMeta, abstractmethod
import threading

from enum import Enum


class State(metaclass=ABCMeta):
    def __init__(self):
        self.transitions = None
        self._env = None

    def set_environment(self, env):
        self._env = env

    @property
    def env(self):
        """
        :return: The simulation environment
        :rtype: simulation.environment.SimulationEnvironment
        """
        return self._env

    @abstractmethod
    def run(self):
        """
        Executes the current state
        :return: The action of the commuter after the execution
        :rtype: simulation.state.CommuterAction
        """
        pass

    def next(self, token):
        """
        Chooses the next state.
        :param token: Used as input to decide which State to transit to.
        :type token: simulation.state.CommuterAction
        :return: The State to change to
        :rtype: simulation.state.CommuterState
        """
        if token in self.transitions:
            return self.transitions[token]
        else:
            raise StateError("Input '%s' not supported for current state" % token.name)


class StateError(Exception):
    pass


class Home(State):
    def run(self):
        c = self.env.commuter
        hour, minute = int(c.leave_time.total_seconds() // 3600), int(c.leave_time.total_seconds() // 60 % 60)
        if self.env.now.weekday() is 5:     # 0 = Monday, 6 = Sunday
            import datetime
            self.env.fast_forward_time(hour, minute, datetime.timedelta(days=2))
        else:
            self.env.fast_forward_time(hour, minute)
        self.env.route = c.work_route
        return CommuterAction.LeavingHome

    def next(self, token):
        if not self.transitions:
            self.transitions = {
                CommuterAction.LeavingHome: CommuterState.Drive
            }
        return super().next(token)


class Work(State):
    def next(self, token):
        if not self.transitions:
            self.transitions = {
                CommuterAction.LeavingWork: CommuterState.Drive
            }
        return super().next(token)

    def run(self):
        import datetime as dt
        self.env.route = self.env.commuter.home_route
        self.env.consume_time(dt.timedelta(hours=8))
        return CommuterAction.LeavingWork


class Driving(State):
    def next(self, token):
        if not self.transitions:
            self.transitions = {
                CommuterAction.ArrivedAtWork: CommuterState.Work,
                CommuterAction.ArrivedAtHome: CommuterState.Home,
                CommuterAction.ArrivedAtFillingStation: CommuterState.Refill,
                CommuterAction.SearchFillingStation: CommuterState.Search
            }
        return super().next(token)

    def run(self):
        self.env.route.reset()
        return self.env.car.drive()


class SearchingFillingStation(State):
    def next(self, token):
        return CommuterState.Drive

    def run(self):
        destination = self.env.refilling_strategy.find_filling_station()

        from simulation.routing import calculation as rc
        self.env.route = rc.calculate_route(self.env.car.current_position, destination, CommuterAction.ArrivedAtFillingStation)

        return CommuterAction.ArrivedAtFillingStation


class Refill(State):
    def next(self, token):
        return CommuterState.Drive

    def run(self):
        self.env.refilling_strategy.refill()
        if self.env.is_driving_to_work:
            destination = self.env.commuter.work_route.destination
            action = CommuterAction.ArrivedAtWork
        else:
            destination = self.env.commuter.home_route.destination
            action = CommuterAction.ArrivedAtHome

        from simulation.routing import calculation as rc
        self.env.route = rc.calculate_route(self.env.route.destination, destination, action)
        return CommuterAction.LeavingFillingStation


class Initialize(State):
    def next(self, token):
        return CommuterState.Home

    def run(self):
        pass


class End(State):
    def next(self, token):
        return self

    def run(self):
        raise StopIteration


class CommuterAction(Enum):
    ArrivedAtHome = 10
    ArrivedAtWork = 11
    ArrivedAtFillingStation = 12
    LeavingHome = 20
    LeavingWork = 21
    LeavingFillingStation = 22
    SearchFillingStation = 30
    FoundFillingStation = 31
    RefilledCar = 32
    FinishedSimulation = 9999


CommuterState = threading.local()


def initialize_states():
    CommuterState.Start = Initialize()
    CommuterState.Finish = End()
    CommuterState.Drive = Driving()
    CommuterState.Home = Home()
    CommuterState.Work = Work()
    CommuterState.Refill = Refill()
    CommuterState.Search = SearchingFillingStation()


def initialize_states_environment(env):
    CommuterState.Start.set_environment(env)
    CommuterState.Finish.set_environment(env)
    CommuterState.Drive.set_environment(env)
    CommuterState.Home.set_environment(env)
    CommuterState.Work.set_environment(env)
    CommuterState.Refill.set_environment(env)
    CommuterState.Search.set_environment(env)

