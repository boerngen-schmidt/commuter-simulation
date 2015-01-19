"""
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
"""
from abc import ABCMeta, abstractmethod
import random
import datetime

from routing.route import RouteFragment, Route
from simulation.environment import SimulationEnvironment
from simulation.event import SimEvent, Event


class BaseCar(metaclass=ABCMeta):
    """
    Represents a car
    """
    def __init__(self, commuter_id, env: SimulationEnvironment, tank_size):
        """
        Constructor
        """
        env.car(self)
        self.env = env
        self.id = commuter_id
        self._tankFilling = BaseCar._random_tank_filling(tank_size)
        self._tankSize = tank_size
        #self.log = logging.getLogger('spritsim.Car' + commuter_id)

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

    @abstractmethod
    def consume_fuel(self, speed, distance, road_type):
        pass

    @abstractmethod
    def drive(self, route: Route, event: Event) -> SimEvent:
        """Lets the car drive the given route

         On arrival at the destination the a SimEvent is

        :param route: Route that should be driven
        :param event: The event that will be returned on successfully driving the given route
        :return: An event to indicate the result of the driving
        :rtype SimEvent:
        """
        pass

    def _do_driving(self, segment: RouteFragment):
        """
        Drives the given route segment

        Uses the segment data to simulate the driving of the car. Thereby fuel is consumed to the amount calculated
        by the

        :param segment: a single fragment of the route
        :type segment RouteFragment:
        """
        self.consume_fuel(segment.speed_limit, segment.length, segment.road_type)


class SimpleCar(BaseCar):
    def __init__(self, commuter_id, env: SimulationEnvironment):
        super().__init__(commuter_id, env, 50)

    def consume_fuel(self, speed, distance, road_type):
        """Consumes standard of 10l per 100km"""
        consumption = 50 / 500
        self._tankFilling -= consumption * distance

    def drive(self, route: Route, event: Event):
        time = datetime.timedelta()
        for segment in route:
            self._do_driving(segment)
            time += datetime.timedelta(seconds=segment.travel_time)

            # check if driving the segment has
            if self._tankFilling <= 5:
                event_data = dict(route_start=route.start,
                                  route_destination=route.destination,
                                  current_position=segment.target,
                                  time_driven=time,
                                  route_event=route.event_type
                )
                return SimEvent(Event.ReserveTank, event_data)

        event_data = dict(time_driven=time)
        return SimEvent(event, event_data)