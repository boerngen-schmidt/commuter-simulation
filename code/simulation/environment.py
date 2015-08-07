import datetime as dt

from simulation.commuter import Commuter


class SimulationEnvironment:
    """Simulation environment is also the context of the StateMachine"""
    def __init__(self, start_time, commuter_id, rerun):
        """Initialization of the SimulationEnvironment.

        :param start_time: Start time of the SimulationEnvironment
        :type start_time: datetime.datetime
        :param rerun: Indicator if the commuter is simulated again with a different strategy
        :type rerun: bool
        """
        self._result = ResultCollector()
        self._current_route = None
        self._car = None
        self._refill_strategy = None
        self._time = start_time
        self._to_work = True
        self._rerun = rerun

        # Initialize the commuter
        self._commuter = Commuter(commuter_id, self)

    @property
    def result(self):
        return self._result

    @property
    def rerun(self):
        return self._rerun

    @property
    def now(self):
        """

        :return: Current time of the SimulationEnvironment
        :rtype: datetime.datetime
        """
        return self._time

    @property
    def is_driving_to_work(self):
        """
        :return: Indication if the commuter is driving to work or home
        :rtype: bool
        """
        return self._to_work

    def consume_time(self, amount):
        """Consumes an amount of time in the simulation

        :param amount: The amount of time to consume
        :type amount: datetime.timedelta
        """
        self._time += amount

    def fast_forward_time(self, to_hour, to_minute, delta=dt.timedelta(days=1)):
        """Fast forwards the time to given hour and minute by a day

        :param to_hour: hour to fast forward to
        :type to_hour: int
        :param to_minute: minute to fast forward to
        :type to_minute: int
        :param delta: a timedelta which is added after datetime was set to hour and minute. (Default: 1 day)
        :type delta: datetime.timedelta
        :return:
        """
        self._time = self.now.replace(hour=to_hour, minute=to_minute) + delta

    @property
    def commuter(self):
        """Returns the commuter of the simulation environment

        :return: The Commuter of the environment
        :rtype: simulation.commuter.Commuter
        """
        return self._commuter

    @commuter.setter
    def commuter(self, commuter):
        """Sets the commuter of the environment

        :param commuter: The commuter for the environment
        :type commuter: simulation.commuter.Commuter
        :return:
        """
        self._commuter = commuter

    @property
    def route(self):
        """
        :rtype: simulation.routing.route.Route
        :return: The current Route of the commuter and its car
        """
        return self._current_route

    @route.setter
    def route(self, route):
        """Set the route which should be driven on
        :param route: The route to drive on
        :type route: simulation.routing.route.Route
        """
        from simulation.routing.route import RouteType
        if route.route_type is RouteType.Work:
            self._to_work = True
        elif route.route_type is RouteType.Home:
            self._to_work = False
        self._current_route = route

    @property
    def car(self):
        """
        :return: The Car the commuter drives
        :rtype: simulation.car.BaseCar
        """
        return self._car

    @car.setter
    def car(self, car):
        """
        :param car: The car the commuter drives
        :type car: simulation.car.BaseCar
        """
        self._car = car

    @property
    def refilling_strategy(self):
        """
        :return: The refilling strategy to find stations and refill the car
        :rtype: simulation.strategy.BaseStrategy
        """
        return self._refill_strategy

    @refilling_strategy.setter
    def refilling_strategy(self, refilling_strategy):
        self._refill_strategy = refilling_strategy


class ResultCollector(object):
    def __init__(self):
        self.commuter = {
            'c_id': None,
            'rerun': False,
            'leaving_time': None,
            'route_home_distance': None,
            'route_work_distance': None,
            'fuel_type': None,
            'tank_filling': None,
            'error': None,
            'filling_stations': None
        }
        self.refill = []
        self.route = []

    def add_refill(self, c_id, rerun, amount, price, refueling_time, station, fuel_type):
        self.refill.append(
            {
                'c_id': c_id,
                'rerun': rerun,
                'amount': amount,
                'price': float(price),
                'refueling_time': refueling_time.strftime('%Y-%m-%d %H:%M:%S%z'),
                'station': station,
                'fuel_type': fuel_type
            }
        )

    def add_route(self, commuter_id, rerun, clazz, avg_kmh, km, work):
        self.route.append(
            {
                'c_id': commuter_id,
                'rerun': rerun,
                'clazz': clazz,
                'avg_kmh': avg_kmh,
                'km': km,
                'work_route': work
            }
        )

    def set_commuter(self, c_id, rerun, leaving_time, route_home, route_work, fuel_type, tank_filling, driven_distance):
        self.commuter['c_id'] = c_id
        self.commuter['rerun'] = rerun
        self.commuter['leaving_time'] = str(leaving_time)
        self.commuter['route_home_distance'] = route_home
        self.commuter['route_work_distance'] = route_work
        self.commuter['fuel_type'] = fuel_type
        self.commuter['tank_filling'] = tank_filling
        self.commuter['driven_distance'] = driven_distance

    def set_commuter_filling_stations(self, stations):
        """Add filling stations to commuter

        :param stations: list with stations
        :type stations: list
        """
        self.commuter['filling_stations'] = stations

    def set_commuter_error(self, error):
        self.commuter['error'] = error

    def to_json(self):
        import json
        return json.dumps({'commuter': self.commuter, 'route': self.route, 'refill': self.refill})
