'''
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
'''
import logging

from random import randint


class BaseCar(object):
    """
    Represents a car
    """

    def __init__(self, commuter_id, route, tank_size, refill_strategy):
        """
        Constructor
        """
        self.id = commuter_id
        self.__tankFilling = self.randomTankFilling
        self.__tankSize = tank_size
        self.__strategy = refill_strategy
        self.log = logging.getLogger('spritsim.Car' + commuter_id)
        self.__route = route

    @property
    def randomTankFilling(self):
        """
        Method for initializing a cars with a random tank filling
        between 10 and 100%
        """
        return (randint(10,100)/100)
    
    def canDrive(self):
        """
        checks if a refill event has to be generated
        """
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


class SimpleCar(BaseCar):
    def __init__(self, commuter_id, route, refill_strategy):
        super().__init__(commuter_id, route, 50, refill_strategy)