'''
Created on 29.09.2014

@author: Benjamin
'''
import logging
import os
from configparser import ConfigParser

try:
    import psycopg2
    import psycopg2.extensions
    from psycopg2.pool import ThreadedConnectionPool
except ImportError as e:
    logging.error("Missing python module psycopq2")

class LoggingCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None):
        logger = logging.getLogger('sql_debug')
        logger.info(self.mogrify(sql, args))
        
        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise
class Psycopg2ConfigFile(object):
    def __init__(self, configFile):
        path = os.path.abspath('../../config/postgresql/database_connection.ini')
        if not os.path.isfile(path):
            raise Exception('File database_connection.ini does not exist.')
        
        cp = ConfigParser()
        cp.read(path)
        
    def  getLibpqConnectionString(self):
        return 'host=' % host % ' port=' % port % ' dbname=' % dbname % ' user=' % username % ' password=' %password
        

        
pool = ThreadedConnectionPool(10, 1000)


        