"""
Created on 25.08.2014

@author: Benjamin Börngen-Schmidt
"""
import logging
import logging.config

import simpy.rt
from helper import database as db


def main():
    init_logging()
    print("Hello World")

    env = simpy.rt.RealtimeEnvironment()
    with db.get_connection() as conn:
        curs = conn.cursor()
        curs.execute('SELECT * ')
        for commuter in curs.fetchall():
            env.process()

    env.run()


def init_logging():
    """Initialize logging module
    """
    from helper import file_finder
    import yaml

    try:
        cfg_file = file_finder.find('logging.conf')
        with open(cfg_file, 'rt') as f:
            cfg= yaml.load(f.read())
            logging.config.dictConfig(cfg)
    except:
        raise
    

if __name__ == '__main__':
    main()