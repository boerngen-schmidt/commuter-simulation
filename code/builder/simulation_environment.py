'''
Generates Simulation Environment

@author: Benjamin
'''
from builder.matching import match_points
from builder.points import create_points
from builder.routes import generate_routes
from helper import logger


def main():
    logger.setup()
    create_points()
    match_points()
    generate_routes()


if __name__ == "__main__":
    main()
