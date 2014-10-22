'''
Created on 28.09.2014

@author: Benjamin
'''
import logging

class SimulationEnvironmentBuilder(object):
    '''
    Builds and initializes the simulation environment
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.logger = logging.getLogger('spritsim.EnvironmentBuilder')
        
    def buildEvnvironment(self):
        '''
        Build an environment for the simulation
        '''
        
        pass
    
    def __getGemeindenInKreis(self):
        '''
        Get all the Gemeinden within a certain Kreis
        '''
        sql = 'SELECT * FROM de_commuter_gemeinden WHERE ST_WithIn(geom, (SELECT geom FROM de_commuter_kreise WHERE name LIKE \'Vogelsberg%\'))'
        pass
        
        