'''
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
'''
from routing.route import Route
import random


class Car(object):
    '''
    Represents a car
    '''

    def __init__(self, Route):
        '''
        Constructor
        '''
        self.tankFilling = self.randomTankFilling()
        self.position
        pass
    
    def randomTankFilling(self):
        '''
        Method for initializing a car with a random tank filling
        between 10 and 100%
        '''
        return (random.randint(10,100)/100)
    
    def canDrive(self):
        '''
        checks if a refill event has to be generated
        '''
        pass
        
    def driveRoute(self, toDestination=True):
        '''
        Drives the given route.
        
        toDesination indicates the driving direction
        '''
        pass
        