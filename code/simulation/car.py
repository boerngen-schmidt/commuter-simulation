"""
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
"""
from abc import ABCMeta, abstractmethod
import random
import datetime


class BaseCar(metaclass=ABCMeta):
    """
    Represents a car
    """
    def __init__(self, commuter_id, env, tank_size):
        """
        Constructor
        :type tank_size: int
        :type env: simulation.environment.SimulationEnvironment
        :type commuter_id: int
        """
        env.car = self
        self.env = env
        self.id = commuter_id
        self._tankSize = float(tank_size)
        self._tankFilling = BaseCar._random_tank_filling(self._tankSize)
        self._current_position = None
        # self.log = logging.getLogger('spritsim.Car' + commuter_id)

    @staticmethod
    def _random_tank_filling(maximum):
        """
        Returns a random tank filling in litre

        Method for initializing a cars with a random tank filling between 10 and maximum litres
        :param maximum: maximum tank capacity
        :return: A random filling
        :rtype: float
        """
        return random.uniform(10, maximum)

    @property
    def current_position(self):
        """Returns the nodes target ID
        :rtype: int
        """
        return self._current_position

    @property
    def tank_size(self):
        """

        :return: Size of the car's tank in litre
        :rtype: float
        """
        return self._tankSize

    @property
    def current_filling(self):
        """

        :return: Current filling of the car's tank
        :rtype: float
        """
        return self._tankFilling

    @abstractmethod
    def consume_fuel(self, speed, distance, road_type):
        pass

    @property
    @abstractmethod
    def consumption_per_km(self):
        pass

    def refilled(self):
        """Car has been refilled at a filling station"""
        self._tankFilling = self._tankSize

    @abstractmethod
    def drive(self):
        """Lets the car drive the given route

         On arrival at the destination the a CommuterAction for the route is returned or if the car needs refilling
         the action to search for a refilling station is returned.
        :return: An action to indicate the result of the driving
        :rtype: simulation.enums.CommuterAction:
        """
        pass

    def _do_driving(self, segment):
        """
        Drives the given route segment

        Uses the segment data to simulate the driving of the car. Thereby fuel is consumed to the amount calculated
        by the consume_fuel method.

        :param segment: a single fragment of the route
        :type segment: simulation.routing.route.RouteFragment
        """
        self.consume_fuel(segment.speed_limit, segment.length, segment.road_type)
        self._current_position = segment.target


class SimpleCar(BaseCar):
    def __init__(self, commuter_id, env):
        super().__init__(commuter_id, env, 50)

    @property
    def consumption_per_km(self):
        """Consumes standard of 10l per 100km"""
        return 50 / 500

    def consume_fuel(self, speed, distance, road_type):
        self._tankFilling -= self.consumption_per_km * distance

    def drive(self):
        from simulation import CommuterAction
        for segment in self.env.route:
            self._do_driving(segment)
            self.env.consume_time(datetime.timedelta(seconds=segment.travel_time))

            # check if driving the segment has
            if self._tankFilling <= 5.0 and self.env.route.action is not CommuterAction.ArrivedAtFillingStation:
                return CommuterAction.SearchFillingStation
        return self.env.route.action