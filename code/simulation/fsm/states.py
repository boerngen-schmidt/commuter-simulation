from simulation.fsm import Transitions, UnknownTransitionCondition
from .core import State


class Start(State):
    def enter(self):
        self._setup_environment()

    def execute(self):
        self.fsm.set_transition(Transitions.ArriveAtHome)

    def _setup_environment(self):
        import random
        from database import connection as db
        from simulation.car import PetrolCar, DieselCar
        from simulation.strategy import SimpleRefillStrategy, CheapestRefillStrategy

        if self.fsm.env.rerun:
            from psycopg2.extras import NamedTupleCursor
            with db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                args = dict(c_id=self.fsm.env.commuter.id)
                cur.execute('SELECT * FROM de_sim_data_commuter WHERE c_id = %(c_id)s AND NOT rerun', args)
                result = cur.fetchone()
                conn.commit()
                if result:
                    if result.fuel_type == 'e5':
                        car = PetrolCar(self.fsm.env)
                    else:
                        car = DieselCar(self.fsm.env)
                    car._tankFilling = result.tank_filling
                    self.fsm.env.commuter._leave = result.leaving_time
                    CheapestRefillStrategy(self.fsm.env)
        else:
            if random.random() > 0.5:
                PetrolCar(self.fsm.env)
            else:
                DieselCar(self.fsm.env)
            SimpleRefillStrategy(self.fsm.env)


class End(State):
    def enter(self):
        self.fsm.env.commuter.save_result()

    def execute(self):
        # raise StopIteration
        pass


class Home(State):
    def execute(self):
        """
        Commuter consumes time while he is at home
        """
        c = self.fsm.env.commuter
        hour, minute = int(c.leave_time.total_seconds() // 3600), int(c.leave_time.total_seconds() // 60 % 60)
        if self.fsm.env.now.weekday() is 5:     # 0 = Monday, 6 = Sunday
            import datetime
            self.fsm.env.fast_forward_time(hour, minute, datetime.timedelta(days=2))
        else:
            self.fsm.env.fast_forward_time(hour, minute)

        # set transition
        self.fsm.set_transition(Transitions.DriveToWork)

    def exit(self):
        """
        After the commuter has consumed time at home he drives back to work
        """
        self.fsm.env.route = self.fsm.env.commuter.work_route


class Work(State):
    def execute(self):
        """
        Commuter does consume time while he is at work
        """
        import datetime
        self.fsm.env.consume_time(datetime.timedelta(hours=8))

        # set transition
        self.fsm.set_transition(Transitions.DriveToHome)

    def exit(self):
        self.fsm.env.route = self.fsm.env.commuter.home_route


class Drive(State):
    def __init__(self, fsm):
        super().__init__(fsm)
        self._prev_transition = None

    def enter(self):
        self._prev_transition = self.fsm.transition.name

        # ensure that the route is reset
        self.fsm.env.route.reset()

    def execute(self):
        """
        Commuter drives the car to a location which is either:
         - Work
         - Home
         - FillingStation
        """
        from simulation.car import RefillWarning

        ignore_refill_warning = False
        transition = None

        if self._prev_transition is Transitions.DriveToFillingStation:
            transition = Transitions.ArriveAtFillingStation
            ignore_refill_warning = True
        elif self._prev_transition is Transitions.DriveToHome:
            transition = Transitions.ArriveAtHome
        elif self._prev_transition is Transitions.DriveToWork:
            transition = Transitions.ArriveAtWork
        else:
            raise UnknownTransitionCondition("Unknown transition condition: %s" % self._prev_transition)

        try:
            self.fsm.env.car.drive(ignore_refill_warning)
        except RefillWarning:
            transition = Transitions.SearchFillingStation
        finally:
            self.fsm.set_transition(transition)

    def exit(self):
        self._prev_transition = None


class SearchFillingStation(State):
    def __init__(self, fsm):
        super().__init__(fsm)
        self.prev_destination = None

    def enter(self):
        self.prev_destination = self.fsm.env.route.destination
        """TODO fix the route saving"""

    def execute(self):
        """
        Choose a filling station with the current strategy of the commuter.
        Calculate a route to the filling station
        """
        start = self.fsm.env.car.current_position
        destination = self.fsm.env.refilling_strategy.find_filling_station()

        from simulation.routing import calculation as rc
        self.fsm.env.route = rc.calculate_route(start, destination)

        self.fsm.set_transition(Transitions.DriveToFillingStation)


class FillingStation(State):
    def enter(self):

        pass

    def execute(self):
        self.fsm.env.refilling_strategy.refill()

        if self.fsm.env.is_driving_to_work:
            destination = self.fsm.env.commuter.work_route.destination
            self.fsm.set_transition(Transitions.DriveToWork)
        else:
            destination = self.fsm.env.commuter.home_route.destination
            self.fsm.set_transition(Transitions.DriveToHome)

        from simulation.routing import calculation as rc
        self.fsm.env.route = rc.calculate_route(self.fsm.env.route.destination, destination)

    def exit(self):
        pass
