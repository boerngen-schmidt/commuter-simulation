import datetime as dt


__author__ = 'benjamin'


class SimulationEnvironment():
    def __init__(self, initial_time: dt.datetime):
        self._current_route = None
        self._commuter = None
        self._car = None
        self._refill_strategy = None
        self._event = None
        assert isinstance(initial_time, dt.datetime)
        self._time = initial_time

    def run(self, until: dt.datetime):
        self.commuter.simulate(until)

    @property
    def now(self) -> dt.datetime:
        return self._time

    def consume_time(self, amount: dt.timedelta):
        self._time += amount

    def fast_forward_time(self, to_hour, to_minute, delta: dt.timedelta=dt.timedelta(days=1)):
        """Fast forwards the time to given hour and minute by a day

        :param to_hour: hour to fast forward to
        :param to_minute: minute to fast forward to
        :param delta: a timedelta which is added after datetime was set to hour and minute
        :return:
        """
        self._time = self._time.replace(hour=to_hour, minute=to_minute) + delta

    @property
    def current_event(self):
        return self._event

    @property
    def commuter(self):
        """Returns the commuter of the simulation environment

        :return: The Commuter of the environment
        :rtype simulation.commuter.Commuter:
        """
        return self._commuter

    @commuter.setter
    def commuter(self, commuter):
        from simulation.commuter import Commuter
        if not isinstance(commuter, Commuter):
            raise ValueError('Expected object to be an instance of simulation.commuter.Commuter')
        self._commuter = commuter

    @property
    def route(self):
        return self._current_route

    @route.setter
    def route(self, route):
        self._current_route = route

    @property
    def car(self):
        return self._car

    @car.setter
    def car(self, car):
        self._car = car

    @property
    def refilling_strategy(self):
        return self._refill_strategy

    @refilling_strategy.setter
    def refilling_strategy(self, refilling_strategy):
        self._refill_strategy = refilling_strategy
