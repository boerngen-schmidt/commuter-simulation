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
import datetime as dt


tz = dt.timezone(dt.timedelta(hours=1))


class Commuter(object):
    """The Commuter is a statemachine which transists into different states depending on the environment"""

    def __init__(self, commuter_id, env):
        """
        Constructor
        :param env: The simulation environment
        :type env: simulation.environment.SimulationEnvironment
        :param commuter_id: Id of the commuter
        :type commuter_id: int
        """
        self._id = commuter_id
        env.commuter = self  # set the commuter in its environment
        self.env = env

        # Generate a random leaving time between 6 and 9 o'clock with a 5min interval
        self._leave = dt.timedelta(seconds=random.randrange(6 * 60 * 60, 9 * 60 * 60, 5 * 60))

        self._work_route = None
        ''':type : simulation.routing.route.Route'''
        self._home_route = None
        ''':type : simulation.routing.route.Route'''
        self._setup_routes()

        # Init done save to simulation result
        self.env.result.set_commuter(
            self._id,
            self.env.rerun,
            self._leave,
            self._home_route.distance,
            self._work_route.distance,
            self.env.car.fuel_type,
            self.env.car.current_filling
        )

    def _setup_routes(self):
        """Initializes the two main routes the commuter drives."""
        from simulation import rc
        try:
            self._home_route = rc.route_home(self.env)
            self._work_route = rc.route_to_work(self.env)
        except:
            raise
        else:
            self.env.route = self._work_route

    def override_parameters(self, leave_time):
        self._leave = leave_time
        # Also overwrite the result set to comply with the overwritten parameters
        self.env.result.set_commuter(
            self._id,
            self.env.rerun,
            self._leave,
            self._home_route.distance,
            self._work_route.distance,
            self.env.car.fuel_type,
            self.env.car.current_filling
        )

    @property
    def id(self):
        return self._id

    @property
    def work_route(self):
        """

        :return: The route to work
        :rtype: simulation.routing.route.Route
        """
        return self._work_route

    @property
    def home_route(self):
        """

        :return: The route home
        :rtype: simulation.routing.route.Route
        """
        return self._home_route

    @property
    def leave_time(self):
        """

        :return: The time commuter leaves for work
        :rtype: datetime.timedelta
        """
        return self._leave


class CommuterError(Exception):
    pass


class CommuterRouteError(CommuterError):
    pass