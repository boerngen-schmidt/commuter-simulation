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

from database import connection as db


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

        self._work_route = None
        ''':type : simulation.routing.route.Route'''
        self._home_route = None
        ''':type : simulation.routing.route.Route'''
        self._setup_routes(commuter_id)

        # Generate a random leaving time between 6 and 9 o'clock with a 5min interval
        self._leave = dt.timedelta(seconds=random.randrange(6 * 60 * 60, 9 * 60 * 60, 5 * 60))

        if not env.rerun:
            self._safe_commuter_info()

    def _safe_commuter_info(self):
        # Save Information into DB
        args = dict(
            id=self._id,
            rerun=self.env.rerun,
            leave_time=self._leave,
            home=(0 if not self._home_route.distance else self._home_route.distance),
            work=(0 if not self._work_route.distance else self._work_route.distance),
            fuel_type=self.env.car.fuel_type,
            filling=self.env.car.current_filling
        )

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO de_sim_data_commuter(c_id, rerun, leaving_time, route_home_distance, route_work_distance, fuel_type, tank_filling) '
                'VALUES (%(id)s, %(rerun)s, %(leave_time)s, %(home)s, %(work)s, %(fuel_type)s, %(filling)s)',
                args)
            conn.commit()

    def _setup_routes(self, route_id):
        """Initializes the two main routes the commuter drives."""
        from simulation import rc
        try:
            self._home_route = rc.route_home(route_id)
            self._work_route = rc.route_to_work(route_id)
        except:
            raise
        else:
            self.env.route = self._work_route

    def override_parameters(self, leave_time):
        self._leave = leave_time

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