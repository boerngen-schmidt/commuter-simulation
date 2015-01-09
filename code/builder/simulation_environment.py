'''
Generates Simulation Environment

@author: Benjamin
'''
import argparse

from builder.actions.match import match_points
from builder.actions.point_creation import create_points
from builder.actions.route_calculation import generate_routes
from helper import logger


def main(args):
    logger.setup()

    if args.create_points:
        create_points()
    if args.match_points:
        match_points()
    if args.generate_routes:
        generate_routes()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Options for building the simulation environment.')
    parser.add_argument('--create-points', help='creates points for the simulation environment', action='store_true')
    parser.add_argument('--match-points', help='matches start and destionation points for simulation environment',
                        action='store_true')
    parser.add_argument('--generate_routes', help='generates routs from previously matched points', action='store_true')
    args = parser.parse_args()
    main(args)
