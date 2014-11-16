"""
Created on 29.09.2014

@author: Benjamin
"""
import logging
import logging.config
import threading
import queue
import time

import yaml
from helper import database


COUNTER_LOCK = threading.Lock()
counter = 0


class RoutingPointCreator(threading.Thread):
    """
    Creates new routing start and destination points for the simulation.

    As basis for how many points should be created within a district,
    the data from the Zensus 2011 should be used.
    """
    def __init__(self, name, work_queue):
        """

        :param str name: Name of the thread
        :param Queue work_queue: The work queue
        :return:
        """
        threading.Thread.__init__(self)
        self.setName(name)
        self.logging = logging.getLogger(name)
        self.q = work_queue

    def run(self):
        while not self.q.empty():
            rs = self.q.get()
            with database.get_connection() as con:
                cur = con.cursor()
                sql = 'WITH area AS (SELECT c.*, s.geom FROM de_commuter_gemeinden c JOIN de_shp_gemeinden s ON c.rs = s.rs WHERE c.rs=%s) '
                sql += 'INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , \'start\', RandomPointsInPolygon(area.geom, (area.outgoing + area.within)) FROM area '
                cur.execute(sql, (rs,))
                num = increase_counter()

                cur.execute('SELECT gen FROM de_shp_gemeinden WHERE rs = %s', (rs,))
                logging.debug('(%4d/%d) %s: Created points for Gemeinde "%s"' % (num, total, self.name, cur.fetchone()[0],))

    def _get_total(self):
        with database.get_connection() as con:
            cur = con.cursor()
            cur.execute('SELECT count(*) FROM de_commuter_gemeinden')
            total = cur.fetchone()[0]

def increase_counter():
    global counter
    with COUNTER_LOCK as lock:
        counter += 1
        result = counter
    return result


def main():
    from helper import file_finder

    try:
        cfg_file = file_finder.find('logging.conf')
        with open(cfg_file, 'rt') as f:
            cfg = yaml.load(f.read())
            logging.config.dictConfig(cfg)
    except:
        raise

    gemeinden = None

    q = queue.Queue()

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
        threads.append(RoutingPointCreator('Thread %s' % i, q))
        threads[-1].start()

    #wait for all threads to finish
    for t in threads:
        t.join()

    end = time.time()
    logging.info('Runtime: %s' % (end-start,))


if __name__ == "__main__":
    main()