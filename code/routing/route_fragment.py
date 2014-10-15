'''
Created on 06.10.2014

@author: Benjamin
'''

class RouteFragment(object):
    '''
    Represents a Fragment of the Route
    '''


    def __init__(self, fragment_id, speed, distance):
        '''
        Constructor
        '''
        self.fragment_id = fragment_id
        # Check Parameters
        if (speed <= 0):
            raise ValueError('Value of speed cannot be negative')
        
        if (distance <= 0):
            raise ValueError('Value of distance cannot be negative')
        
        #
        # Class attributes
        #
        self.speed = speed              # km/h
        self.distance = distance        # km
        self.time = self.distance / self.speed
        
    def getTime(self, resource_modifier=1):
        '''
        Returns the time needed to drive
        '''
        return self.time