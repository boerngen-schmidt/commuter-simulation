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

from simulation.routing import calculation as rc
from simulation.environment import SimulationEnvironment
from simulation.event import Event, SimEvent
from database import connection as db


tz = dt.timezone(dt.timedelta(hours=1))


class Commuter(object):
    """The Commuter is a statemachine which transists into different states depending on the environment"""

    def __init__(self, commuter_id, env: SimulationEnvironment):
        """
        Constructor
        :param env: The simulation environment
        :param commuter_id: Id of the commuter
        """
        self._id = commuter_id
        env.commuter = self  # set the commuter in its environment
        self.env = env

        self._work_route = None
        self._home_route = None
        self._setup_routes(commuter_id)

        # Generate a random leaving time between 6 and 9 o'clock with a 5min interval
        self._leave = dt.timedelta(seconds=random.randrange(6 * 60 * 60, 9 * 60 * 60, 5 * 60))

        # Save Information into DB
        with db.get_connection() as conn:
            cur = conn.cursor()
            leave = dt.datetime.combine(dt.date.today(), dt.time(tzinfo=tz)) + self._leave
            cur.execute(
                'INSERT INTO de_sim_data_commuter VALUES (%s, %s, %s, %s)',
                (commuter_id, leave.time(), self._home_route.distance, self._work_route.distance))
            conn.commit()

    def _setup_routes(self, route_id):
        """Initializes the two main routes the commuter drives."""
        self._home_route = rc.route_home(route_id)
        self._work_route = rc.route_to_work(route_id)

        if not self._home_route.distance or not self._work_route.distance:
            raise CommuterRouteError('No Route found for commuter %s' % self._id)
        else:
            self.env.route = self._work_route

    @property
    def id(self):
        return self._id

    def simulate(self, until):
        """Simulates the Commuter"""
        event = SimEvent(Event.LeavingHome)

        while self.env.now < until:
            # Reset the old route
            self.env.route.reset()

            if event and 'time_driven' in event.data.keys():
                self.env.consume_time(event.data['time_driven'])
            # handle events
            if event.type is Event.Drive:
                '''Default State Drive'''
                event = self.env.car.drive(self.env.route, self.env.route.event_type)
            elif event.type is Event.LeavingHome:
                # Set time to next day leaving time
                hour, minute = int(self._leave.total_seconds() // 3600), int(self._leave.total_seconds() // 60 % 60)
                self.env.fast_forward_time(hour, minute)

                event = SimEvent(Event.Drive)
            elif event.type is Event.ArrivedAtWork:
                self.env.route = self._home_route

                event = SimEvent(Event.FinishedWork)
            elif event.type is Event.ArrivedAtHome:
                self.env.route = self._work_route

                event = SimEvent(Event.LeavingHome)
            elif event.type is Event.RefillCar:
                '''Car hit the reserve'''
                # use refill strategy to find filling station
                self.env.route, station_id, = self.env.refilling_strategy.find_filling_station(event.data)

                event_data = dict(last_event=event.data['route_event'], station_id=station_id)
                event = self.env.car.drive(self.env.route, Event.FillingStation, event_data)
            elif event.type is Event.FillingStation:
                self.env.refilling_strategy.refill(event.data['station_id'])

                if event.data['last_event'] is Event.ArrivedAtHome:
                    destination = self._home_route.destination
                else:
                    destination = self._work_route.destination

                self.env.route = rc.calculate_route(self.env.route.destination, destination, event.data['last_event'])
                event = SimEvent(Event.Drive)
            elif event.type is Event.FinishedWork:
                '''Finished Working'''
                self.env.consume_time(dt.timedelta(hours=8))
                event = SimEvent(Event.Drive)
            else:
                raise CommuterError('No state given')


class CommuterError(Exception):
    pass


class CommuterRouteError(CommuterError):
    pass