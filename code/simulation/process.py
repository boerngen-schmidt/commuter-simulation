import datetime
import multiprocessing as mp

from simulation.cars.car import SimpleCar
from simulation.commuter import Commuter
from simulation.environment import SimulationEnvironment


class CommuterSimulationProcess(mp.Process):
    def __init__(self, commuter_queue: mp.Queue, refill_strategy):
        super().__init__()
        self._q = commuter_queue
        self._refill_strategy = refill_strategy

    def run(self):
        while not self._q.empty():
            c_id = self._q.get()

            # Generate Commuter
            tz = datetime.timezone(datetime.timedelta(hours=1))
            start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
            end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)
            env = SimulationEnvironment(start_time)

            SimpleCar(c_id, env)
            Commuter(c_id, env)
            env.run(end_time)