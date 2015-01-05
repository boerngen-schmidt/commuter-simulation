from multiprocessing import Queue

__author__ = 'benjamin'
from database import connection as db


def __route_feeder_thread(route_queue: Queue, size=200, sentinels=0):
    """Feeder thread for routes

    As the route is the main attribute that describes a commuter the thread will feed the routes to the queue
    one by one to be simulated by the commuter simulation object
    :return:
    """
    sql = 'SELECT * FROM de_sim_routes'
    with db.get_connection() as conn:
        while True:
            cur = conn.cursor()
            cur.execute(sql)
            results = cur.fetchmany(size)
            for rec in results:
                queue.put(rec)
            if sentinels > 0 and not results:
                for i in range(sentinels):
                    queue.put(StopIteration)
                break
            elif not results:
                break