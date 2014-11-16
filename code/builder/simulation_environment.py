'''
Created on 28.09.2014

@author: Benjamin
'''
import logging
import logging.config
import time
import queue

import yaml
from helper import database
from builder import threaded_point_creator as rpc


def main():
    from helper import file_finder

    try:
        cfg_file = file_finder.find('logging.conf')
        with open(cfg_file, 'rt') as f:
            cfg= yaml.load(f.read())
            logging.config.dictConfig(cfg)
    except:
        raise

    gemeinden = None
    q=queue.Queue()

    # Fill the queue
    with database.get_connection() as conn:
        cur = conn.cursor()
        ''':type cur: cursor'''
        cur.execute('SELECT rs FROM de_commuter_gemeinden')

        gemeinden = cur.fetchall()
        for record in gemeinden:
            q.put(record[0])

    threads = []
    start = time.time()
    for i in range(8):
        threads.append(rpc.PointCreator('Thread %s' % i))
        threads[-1].start()

    #wait for all threads to finish
    for t in threads:
        t.join()

    end = time.time()
    logging.info('Runtime: %s' % (end-start,))


if __name__ == "__main__":
    main()