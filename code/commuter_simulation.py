"""
The Simulation purpose is the comparison between using and not using a fuel price application.

To this purpose a simulation environment, containing of start and destination point as well as a road network and
fuel stations, was created. In this environment a commuter will be simulated driving a car from his start point to the
destination. The point in time when the car's tank will be refilled then is chosen through according to the current
strategy of the commuter, which can be either to use a fuel price application or not.

@author: Benjamin Börngen-Schmidt
"""
import multiprocessing as mp

from helper import logger
from routing.route import Route
from simulation.cars.car import SimpleCar


def main():
    logger.setup()

    # fetch all commuters
    commuters = []

    # Generate car and route
    for c in commuters:
        route = Route()
        car = SimpleCar()
        mp.Pool(16, )


if __name__ == '__main__':
    main()