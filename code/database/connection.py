'''
Created on 29.09.2014

@author: Benjamin
'''
import logging

try:
    import psycopg2 as Database
except ImportError as e:
    logging.error("Missing python module psycopq2")

class DatabaseConnection(object):
    '''
    Connection to a database
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        