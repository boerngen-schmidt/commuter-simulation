import datetime
import logging
import multiprocessing as mp
import time

from simulation.cars.car import SimpleCar
from simulation.commuter import Commuter
from simulation.environment import SimulationEnvironment
from simulation.strategy import SimpleRefillStrategy, FillingStationError


class CommuterSimulationProcess(mp.Process):
    def __init__(self, commuter_queue: mp.Queue):
        super().__init__()
        self._q = commuter_queue

    def run(self):
        while not self._q.empty():
            c_id = self._q.get()

            # Generate Commuter
            tz = datetime.timezone(datetime.timedelta(hours=1))
            start_time = datetime.datetime(2014, 6, 1, 0, 0, 0, 0, tz)
            end_time = datetime.datetime(2014, 10, 31, 23, 59, 59, 0, tz)
            env = SimulationEnvironment(start_time)

            # Setup Environment (done by __init__ functions)
            SimpleCar(c_id, env)
            Commuter(c_id, env)
            SimpleRefillStrategy(env)

            start = time.time()
            try:
                env.run(end_time)
            except FillingStationError:
                logging.error('No Fillingstation found for commuter %s', c_id)
            logging.info('Finished commuter %s in %s', c_id, time.time()-start)