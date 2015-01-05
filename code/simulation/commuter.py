'''
Created on 09.10.2014

@author: benjamin
'''


class Commuter(object):
    '''
    Container class for a commuter
    '''


    def __init__(self, commuter_id, route):
        '''
        Constructor
        '''
        self.route = route
        self.car = Car(commuter_id, route)
        
        return
    
    def run(self):
        '''
        Simpy run function
        '''
        
        