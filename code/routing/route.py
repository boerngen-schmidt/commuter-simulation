'''
Created on 25.08.2014

@author: Benjamin Börngen-Schmidt
'''

import psycopg2

class Route(object):
    '''
    Route class stores the information of the route which a commuter uses
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        self.fragments = []
        
    def calculateRoute(self, start, destination):
        '''
        Calculates route
        '''
        sql = 'SELECT pg_dijkstra()'
        jsonRoute = query sql
        self.fragments = self.parseGeoJSON(jsonRoute)
        
        return
    
    def loadRouteFromDatabase(self, route_id):
        '''
        Load a route from database
        '''
        sql = 'SELECT AsGeoJson(geom) FROM de_commuter_routes WHERE route_id='%route_id
        jsonRoute = query sql
        self.fragments = self.parseGeoJSON(jsonRoute)
        
    
    def parseGeoJSON(self, jsonRoute):
        '''
        Parse the returned GeoJSON 
        '''
        pass
    