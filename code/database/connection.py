"""
Created on 29.09.2014

@author: Benjamin Börngen-Schmidt
"""
import logging
import atexit
from contextlib import contextmanager
from configparser import ConfigParser, NoSectionError
from threading import RLock
import os

from psycopg2._psycopg import connection

import psycopg2.extensions
from psycopg2.pool import ThreadedConnectionPool
from helper.file_finder import find





# module Stuff
databaseConfig = None
""" Holds the configuration
:type databaseConfig: _Psycopg2ConnectionPoolConfig
"""

DEFAULT_DATABASE_CONFIGURATION_FILE_NAME='database.conf'
"""Default name for the configuration file
:type DEFAULT_DATABASE_CONFIGURATION_FILE_NAME: string
"""

_logger = logging.getLogger('helper.database')

_database_config_lock = RLock()


class LoggingCursor(psycopg2.extensions.cursor):
    """
    Logging cursor does log any SQL statement that is executed.
    """
    def execute(self, sql, args=None):
        logger = logging.getLogger('database.sql_debug')

        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            logger.error("Query: %s", self.query)
            raise


class _Psycopg2ConnectionPoolConfig(object):
    """
    Private class which holds the configuration for a postgresql connection.
    It also registers the 
    """
    
    __slots__ = ('cp', 'logger', 'pool')
    
    def __init__(self, configFile):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Using configuration file "%s"', configFile)
        
        self.cp = ConfigParser()
        self.cp.read(configFile)

        with _database_config_lock:
            self.pool = self._create_pool()
    
    def _create_pool(self):
        """
        Method creates a connection pool
        """
        if not self.cp.has_section('database'):
            self.logger.critical('Missing [database] section in configuration file.')
            raise NoSectionError('database')
        
        common_dsn = self._get_libpq_connection_string()

        min_conn = self.cp.getint(section='database', option='minconn', fallback=0)
        max_conn = self.cp.getint(section='database', option='maxconn', fallback=10)
        cursor_factory = self.cp.get(section='database', option='cursor_factory', fallback=None)
           
        # try:
        #     _class = getattr(psycopg2.pool, self.cp.get('database', 'pool'))
        # except NoOptionError:
        #     self.logger.error('Missing "pool" in configuration file')
        #     raise
        # except AttributeError:
        #     self.logger.error('Pool class with name "%s" does not exist.', self.cp.get('database', 'pool'))
        #     raise
        #
        # return _class(minconn, maxconn, common_dsn) or None
        atexit.register(self._at_exit_close)
        return ThreadedConnectionPool(min_conn, max_conn, dsn=common_dsn, cursor_factory=cursor_factory)

    def _get_libpq_connection_string(self):
        """
        Generates a libpg compatible connection string.

        http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING
        http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
        """
        exclude = ('dsn', 'minconn', 'maxconn', 'pool', 'cursor_factory')
        return ' '.join( '{0[0]}={0[1]}'.format(item) for item in self.cp.items('database') if item[0].lower() not in exclude )

    def get_pool(self):
        return self.pool

    def _at_exit_close(self):
        if self.pool is not None:
            self.pool.closeall()


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
    file_name = find(file_name)
    # create configuration
    global databaseConfig
    databaseConfig = _Psycopg2ConnectionPoolConfig(os.path.abspath(file_name))


def get_connection_pool():
    """Returns the connection pool.

    If no database is configured, :py:fc:loadConfig will be called to setup the database connection pool.
    :return: The connection pool
    :rtype: ThreadedConnectionPool
    """
    if databaseConfig is None:
        loadConfig()
    return databaseConfig.get_pool()


@contextmanager
def get_connection(key=None) -> connection:
    """Returns a connection from the connection pool to be used within a context

    :param key: Key for the connection
    :return: A connection cursor
    :rtype connection:
    """
    pool = get_connection_pool()
    conn = pool.getconn(key)
    try:
        yield conn
    except Exception:
        conn.rollback()
        _logger.error('Transaction for connection with key "%s" was rolled back.' % (key,))
        raise
    else:
        conn.commit()
    finally:
        pool.putconn(conn)
