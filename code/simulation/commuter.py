"""
A Commuter has the following properties
  - drives a car
  - follow a given route to work
  - has a RefillStrategy
  - works
  - leaves for work at a certain time

@author: benjamin
"""
import random
import datetime

import routing.calculation as rc
from simulation.environment import SimulationEnvironment
from simulation.event import Event


tz = datetime.timezone(datetime.timedelta(hours=1))


class Commuter(object):
    """Container class for a commuter"""
    def __init__(self, commuter_id, env: SimulationEnvironment):
        """
        Constructor
        :param env: The simulation environment
        :param commuter_id: Id of the commuter
        """
        self._id = commuter_id
        env.commuter(self)      # set the commuter in its environment
        self.env = env

        self._work_route = None
        self._home_route = None
        self._setup_routes(commuter_id)

        # Generate a random leaving time between 6 and 9 o'clock with a 5min interval
        self._leave = datetime.timedelta(seconds=random.randrange(6*60*60, 9*60*60, 5*60))

    def _setup_routes(self, route_id):
        self._home_route = rc.route_home(route_id)
        self._work_route = rc.route_to_work(route_id)
        self.env.route = self._work_route

    def simulate(self, until):
        """Simulates the Commuter"""
        event = None
        while self.env.now < until:
            # Reset the old route
            self.env.route.reset()

            # handle events
            if event is Event.ArrivedAtWork:
                self.env.route = self._home_route

                # Update current time
                self.env.consume_time(datetime.timedelta(hours=8) + event.data['time_driven'])

                event = Event.FinishedWork
            elif event is Event.ArrivedAtHome:
                self.env.route = self._work_route

                # Set time to next day leaving time
                hour, minute = self._leave // 3600, self._leave // 60 % 60
                self.env.fast_forward_time(hour, minute)

                event = Event.LeavingHome
            elif event is Event.ReserveTank:
                # use refill strategy to find filling station
                self.env.route = self.env.refilling_strategy.find_filling_station(event.data)

                event = self.env.car.drive(self.env.route)
            elif event is Event.FillingStation:
                self.env.route = rc.calculate_route(event.fata['current_position'],
                                                    event.data['route_destination'],
                                                    event.data['route_event'])

                event = None
            elif event is Event.LeavingHome:
                # Currently this event does nothing
                event = None
            elif event is Event.FinishedWork:
                # Currently this event does nothing
                event = None
            else:
                event = self.env.car.drive(self.env.route)


class CommuterError(Exception):
    pass