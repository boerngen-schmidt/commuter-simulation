'''
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
'''
import logging

from random import randint


class Car():
    """
    Represents a car
    """

    __slots__ = {'currentSpeed', 'tankFilling', 'logger', 'currentPosition', 'currentDirection', 'route'}
    """Use __slots__ to minimize the memory needed for the class, since we will spawn over 40.000.000 of them"""

    def __init__(self, commuter_id, route):
        """
        Constructor
        """
        self.currentSpeed = 0
        self.tankFilling = self.randomTankFilling
        self.logger = logging.getLogger('spritsim.Car' + commuter_id)
        self.currentPosition
        self.currentDirection
        self.route = route
        pass
    
    @property
    def randomTankFilling(self):
        """
        Method for initializing a car with a random tank filling
        between 10 and 100%
        """
        return (randint(10,100)/100)
    
    def canDrive(self):
        """
        checks if a refill event has to be generated
        """
        
        self.logger.info('Random Tank filling')
        pass
    
    def isHeadingHome(self):
        """
        Returns the direction in which the car is heading

        @return: true if car is heading home, false if heading for work
        """
        pass
    
    def findNearestFuelstation(self):
        """
        Takes current car posijtion and direction to search for the nearest fuelstation
        """
        pass
    
    def driveRoute(self, toDestination=True):
        """
        Drives the given route.

        toDesination indicates the driving direction
        """
        pass