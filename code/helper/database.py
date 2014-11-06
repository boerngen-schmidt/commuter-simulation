'''
Created on 29.09.2014

@author: Benjamin Börngen-Schmidt
'''
import logging
from os.path import abspath
from configparser import ConfigParser, NoSectionError, NoOptionError
import psycopg2.extensions
import psycopg2.pool

# module Stuff
databaseConfig = None
DEFAULT_DATABASE_CONFIGURATION_FILE_NAME='database.conf'

class LoggingCursor(psycopg2.extensions.cursor):
    '''
    Logging cursor does log any SQL statement that is executed.
    '''
    def execute(self, sql, args=None):
        logger = logging.getLogger('database.sql_debug')
        logger.info(self.mogrify(sql, args))
        
        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise


class _Psycopg2ConnectionPoolConfig(object):
    '''
    Private class which holds the configuration for a postgresql connection.
    It also registers the 
    '''
    
    __slots__ = ('cp', 'logger', 'pool')
    
    def __init__(self, configFile):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Using configuration file "%s"', configFile)
        
        self.cp = ConfigParser()
        self.cp.read(configFile)
        
        self.pool = self._createPool()
    
    def _createPool(self):
        '''
        Method creates a connection pool
        '''
        if not self.cp.has_section('database'):
            self.logger.critical('Missing [database] section in configuration file.')
            raise NoSectionError('database')
        
        common_dsn = self._getLibpqConnectionString()
        
        try :
            minconn = self.cp.getint('database', 'minconn')
        except NoOptionError:
            minconn = 0
            
        try :
            maxconn = self.cp.getint('database', 'maxconn')
        except NoOptionError:
            maxconn = 10
           
        try:     
            _class = getattr(psycopg2.pool, self.cp.get('database', 'pool'))
        except NoOptionError:
            self.logger.error('Missing "pool" in configuration file')
            raise
        except AttributeError:
            self.logger.error('Pool class with name "%s" does not exist.', self.cp.get('database', 'pool'))
            raise
            
        return _class(minconn, maxconn, common_dsn) or None

    def  _getLibpqConnectionString(self):
        exclude = ('dsn', 'minconn', 'maxconn', 'pool')
        return ' '.join( '{0[0]}={0[1]}'.format(item) for item in self.cp.items('database') if item[0].lower() not in exclude )
        
def loadConfig(file_name=DEFAULT_DATABASE_CONFIGURATION_FILE_NAME):
    """
    Configure database pools from the given configuration file. 
    Database configuration section names should start with prefix 'database_' 
    a name after that prefix is used as name for the registered connection pool.
    
    Configuration file should be named database.conf (default name) and located 
    in the current directory or if not found there in the PYTHON_PATH directories.
    This makes it possible to have one global configuration file, and then 
    add a local one for debugging purposes. Note, that config data is not being 
    merged and the file, first found is being used as a config file.
    
    Typical configuration file can look like that::
        
        [database]
        pool=SimpleConnectionPool
        minconn=0
        maxconn=10
        dbname=testdb 
        host=localhost
        port=5432
        user=test 
        password=test
    
    For more options have a look at these pages::
        http://initd.org/psycopg/docs/pool.html
        http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING
        http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
    """
    # find configuration file
    file_name = find_file
    # create configuration
    global databaseConfig #IGNORE:W0603
    databaseConfig = _Psycopg2ConnectionPoolConfig(abspath(file_name))
