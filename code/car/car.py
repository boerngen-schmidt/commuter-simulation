'''
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
'''
from routing.route import Route
import logging

class Car(object):
    '''
    Represents a car
    '''

    def __init__(self, Route):
        '''
        Constructor
        '''
        self.currentSpeed = 0
        self.tankFilling = 0.05
        self.logger = logging.getLogger('spritsim.Car')
        pass
    
    def randomTankFilling(self):
        '''
        Method for initializing a car with a random tank filling
        '''
        
        self.logger.info('Random Tank filling')
        pass
    
    def isHeadingHome(self):
        '''
        Returns the direction in which the car is heading
        
        @return: true if car is heading home, false if heading for work
        '''
        pass
    
    def findNearestFuelstation(self):
        '''
        Takes current car posijtion and direction to search for the nearest fuelstation
        '''
        pass
    
    
    
    
        