import datetime as dt


class SimulationEnvironment():
    """Simulation environment is also the context of the StateMachine"""
    def __init__(self, initial_time, rerun):
        """

        :param initial_time: Start time of the SimulationEnvironment
        :type initial_time: datetime.datetime
        :return:
        """
        self._current_route = None
        self._commuter = None
        self._car = None
        self._refill_strategy = None
        self._time = initial_time
        ''':type : datetime.datetime'''
        self._to_work = True
        self._rerun = rerun
        self._result = ResultCollector()

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
        """

        :param amount: The amount of time to consume
        :type amount: datetime.timedelta
        :return:
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
        self._time = self._time.replace(hour=to_hour, minute=to_minute) + delta

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
        from simulation import CommuterAction
        if route.action is CommuterAction.ArrivedAtWork:
            self._to_work = True
        elif route.action is CommuterAction.ArrivedAtHome:
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
            'error': ''
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
                'refueling_time': str(refueling_time),
                'station': station,
                'fuel_type': fuel_type
            }
        )

    def add_route(self, commuter_id, rerun, clazz, avg_kmh, km, work):
        self.route.append(
            {
                'commuter_id': commuter_id,
                'rerun': rerun,
                'clazz': clazz,
                'avg_kmh': avg_kmh,
                'km': km,
                'work_route': work
            }
        )

    def set_commuter(self, c_id, rerun, leaving_time, route_home, route_work, fuel_type, tank_filling):
        self.commuter = {
            'c_id': c_id,
            'rerun': rerun,
            'leaving_time': str(leaving_time),
            'route_home_distance': route_home,
            'route_work_distance': route_work,
            'fuel_type': fuel_type,
            'tank_filling': tank_filling,
            'error': ''
        }

    def set_commuter_error(self, error):
        self.commuter['error'] = error

    def to_json(self):
        import json
        return json.dumps({'commuter': self.commuter, 'route': self.route, 'refill': self.refill})