"""
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
"""
from abc import ABCMeta, abstractmethod
import random
import datetime


class BaseCar(metaclass=ABCMeta):
    """
    Represents the fundamentals of a car
    """
    def __init__(self, env, tank_size):
        """
        Constructor
        :type tank_size: int
        :type env: simulation.environment.SimulationEnvironment
        """
        env.car = self
        self.env = env
        self._tankSize = float(tank_size)
        self._tankFilling = BaseCar._random_tank_filling(self._tankSize)
        self._current_position = None
        self._fuel_type = 'e5'
        self._driven_distance = float(0)
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
    def driven_distance(self):
        """
        The car's odometer
        :return: The total distance the car has traveled
        :rtype: float
        """
        return self._driven_distance

    @property
    def fuel_type(self):
        """
        The car's fuel type
        :return: Type of fuel (e5|diesel)
        :rtype: str
        """
        return self._fuel_type

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

    def consume_fuel(self, speed, distance, road_type):
        """

        :param int speed: Maximum allowed speed
        :param float distance: Length of the segment
        :param simulation.routing.route.RouteClazz road_type: The type of the road
        :return:
        """
        self._tankFilling -= self.consumption_per_km * distance

    @property
    @abstractmethod
    def consumption_per_km(self):
        """
        :return: The fuel consumption of the car per km
        :rtype: float
        """
        pass

    @property
    def km_left(self):
        """
        Returns the remaining km the car can drive
        :return: Distance car is able to drive
        :rtype: float
        """
        return self.current_filling / self.consumption_per_km

    def refilled(self):
        """Car has been refilled at a filling station"""
        self._tankFilling = self._tankSize

    def drive(self, ignore_refill_warning=False):
        """Lets the car drive the given route

         On arrival at the destination the a CommuterAction for the route is returned or if the car needs refilling
         the action to search for a refilling station is returned.
        :param ignore_refill_warning: Tells the function not to raise a RefillWarning (default: False)
        :type ignore_refill_warning: bool
        :raises RefillWarning: If the tank filling is less or equal 5.0 liter
        """
        for segment in self.env.route:
            self._do_driving(segment)
            self.env.consume_time(datetime.timedelta(seconds=segment.travel_time))

            # check if driving the segment has
            if self._tankFilling <= 5.0 and not ignore_refill_warning:
                raise RefillWarning()

    def _do_driving(self, segment):
        """
        Drives the given route segment

        Uses the segment data to simulate the driving of the car. Thereby fuel is consumed to the amount calculated
        by the consume_fuel method.

        :param segment: a single fragment of the route
        :type segment: simulation.routing.route.RouteFragment
        """
        self.consume_fuel(segment.speed_limit, segment.length, segment.road_type)
        self._driven_distance += segment.length
        self._current_position = segment.target


class PetrolCar(BaseCar):
    def __init__(self, env):
        super().__init__(env, 50)
        self._fuel_type = 'e5'

    @property
    def consumption_per_km(self):
        """
        Consumes standard of 10 Liter per 100km, an equivalent of 0.1 L/km
        :return: fuel consumption per 1 km in liter
        :rtype: float
        """
        return 0.1


class DieselCar(BaseCar):
    def __init__(self, env):
        super().__init__(env, 50)
        self._fuel_type = 'diesel'

    @property
    def consumption_per_km(self):
        """
        Consumes standard of 8 litre per 100km, an equivalent of 0.08 L/km
        :return: fuel consumption per 1 km in liter
        :rtype: float
        """
        return 0.08

class RefillWarning(Exception):
    pass
