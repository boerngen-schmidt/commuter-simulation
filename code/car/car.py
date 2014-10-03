'''
Created on 11.09.2014

@author: benjamin@boerngen-schmidt.de
'''
from routing.route import Route

class Car(object):
    '''
    Represents a car
    '''
    
    currentSpeed = 0
    tankFilling = 0.05
    


    def __init__(self, Route):
        '''
        Constructor
        '''
        pass
    
    def randomTankFilling(self):
        '''
        Method for initializing a car with a random tank filling
        '''
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
    
    
    
    
        