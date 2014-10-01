'''
Created on 25.08.2014

@author: Benjamin Börngen-Schmidt
'''
import logging

def main():
    init_logging()
    print 'Hello World'
    
def init_logging():
    '''
    Initialize logging module
    '''
    logger = logging.getLogger('sprit_sim')
    logger.setLevel(logging.DEBUG)
    
    # FileHandler for log file
    fh_debug = logging.FileHandler('../logs/debug.log')
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh_debug.setFormatter(formatter)
    
    # add handler to logger
    logger.addHandler(fh_debug)
    

if __name__ == '__main__':
    main()