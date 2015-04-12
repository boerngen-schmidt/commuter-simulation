#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generates Simulation Environment

@author: Benjamin
"""
import argparse

from builder.actions import clean_points, reset_matches
from builder.actions.match_revised import match_points
# from builder.actions.match import match_points
from builder.actions.point_creation import create_points
from builder.actions.route_calculation import generate_routes
from builder.actions.sample_commuters import sample_commuters
from helper import logger


def main(args):
    logger.setup()

    if args.clean_points:
        clean_points.run()
    if args.reset_matches:
        reset_matches.run()

    if args.create_points:
        create_points()
    if args.match_points:
        match_points()
    if args.generate_routes:
        generate_routes()
    if args.sample_commuters:
        sample_commuters()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Options for building the simulation environment.',
                                     epilog='One of the arguments from the Action group must be present')

    parser.add_argument('--clean-points', help='Removes generated start and destination points', action='store_true')
    #parser.add_argument('--reset-points', 'Resets the usage of the points', action='store_true')
    parser.add_argument('--reset-matches', help='Clears already matched points and resets their usage to false',
                        action='store_true')

    actions_group = parser.add_argument_group(title='Actions',
                                              description='Primary actions for simulation environment builder')
    actions_group.add_argument('--create-points', help='creates points for the simulation environment',
                               action='store_true')
    actions_group.add_argument('--match-points', help='matches start and destination points for simulation environment',
                               action='store_true')
    actions_group.add_argument('--generate-routes', help='generates routs from previously matched points',
                               action='store_true')
    actions_group.add_argument('--sample-commuters', help='samples commuters from already matched routes',
                               action='store_true')
    ze_args = parser.parse_args()
    if not any([ze_args.create_points, ze_args.generate_routes, ze_args.match_points, ze_args.sample_commuters]):
        parser.print_help()
        quit()

    main(ze_args)
