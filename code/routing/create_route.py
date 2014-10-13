'''
Created on 03.10.2014

@author: Benjamin
'''

class CreateRoute(object):
    '''
    Calculates route for a car, saves route into database
    '''


    def __init__(self, start_point, destination_point):
        '''
        Constructor
        '''
        pass
    
    def saveToDatabase(self):
        '''
        saves created route to database
        '''
        conn = psycopg2 
        pass
    
    def createRoute(self):
        '''
            SELECT seq, id1 AS node, id2 AS edge, cost, b.the_geom FROM pgr_dijkstra('
                    SELECT gid AS id,
                             source::integer,
                             target::integer,
                             length::double precision AS cost
                            FROM ways',
                    30, 60, false, false) a LEFT JOIN ways b ON (a.id2 = b.gid);
        '''
        
        