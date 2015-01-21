"""
The Simulation purpose is the comparison between using and not using a fuel price application.

To this purpose a simulation environment, containing of start and destination point as well as a road network and
fuel stations, was created. In this environment a commuter will be simulated driving a car from his start point to the
destination. The point in time when the car's tank will be refilled then is chosen through according to the current
strategy of the commuter, which can be either to use a fuel price application or not.

@author: Benjamin Börngen-Schmidt
"""
import multiprocessing as mp

from database import connection as db
from helper import logger
from simulation.process import CommuterSimulationProcess


def main():
    logger.setup()

    # fetch all commuters
    commuter_sim_queue = mp.Queue()

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM de_sim_routes LIMIT 100')
        [commuter_sim_queue.put(rec[0]) for rec in cur.fetchall()]

    processes = []
    for i in range(1):
        processes.append(CommuterSimulationProcess(commuter_sim_queue))
        processes[-1].start()

    for p in processes:
        p.join()


if __name__ == '__main__':
    main()