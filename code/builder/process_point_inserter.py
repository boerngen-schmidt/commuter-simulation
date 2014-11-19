import logging
import time
from multiprocessing.queues import Queue, JoinableQueue
from multiprocessing import Process, Event
from queue import Empty
from threading import Thread

from helper import database


class PointInsertingProcess(Process):
    def __init__(self, input_queue: JoinableQueue):
        Process.__init__(self)
        self.q = input_queue
        self.thread_queue = Queue()
        self.batch_size = 30000
        self.insert_threads = 2
        self.stop_request = Event()
        self.logging = logging.getLogger(self.name)

    def set_batch_size(self, value: int):
        self.batch_size = value

    def set_insert_threads(self, value: int):
        self.insert_threads = value

    def run(self):
        """Overwritten run method

        Process will run until the input queue is closed
        """
        threads = []
        for i in range(self.insert_threads):
            name = 'Inserting Thread %s' % i
            t = PointInsertingThread(self.thread_queue, self.stop_request)
            t.setName(name)
            threads.append(t)
            t.start()

        sql_commands = []
        while True:
            try:
                sql_commands.append(self.q.get(block=True, timeout=0.5))
            except Empty:
                # Nothing there yet, check Event and wait for data again
                self.logging.debug('Queue size %s, Event %s', self.q.qsize(), self.stop_request.is_set())
                continue
            else:
                if len(sql_commands) >= self.batch_size:
                    self.thread_queue.put(sql_commands)
                    del sql_commands[:]
                self.q.task_done()
            finally:
                if self.stop_request.is_set():
                    self.logging.info('Recieved stop event. Queue size %s, SQL commands %s',
                                      self.q.qsize(), len(sql_commands))
                    while not self.q.empty():
                        sql_commands.append(self.q.get())
                        self.q.task_done()
                    self.thread_queue.put(sql_commands)
                    del sql_commands

                    self.logging.info('Doing last inserts. Queue size %s, SQL commands %s',
                                      self.q.qsize(), len(sql_commands))
                    break

        for t in threads:
            t.join()

    def stop(self):
        self.stop_request.set()

    def join(self, timeout=None):
        self.stop_request.set()
        super(PointInsertingProcess, self).join(timeout)


class PointInsertingThread(Thread):
    def __init__(self, queue: Queue, stop_request: Event):
        Thread.__init__(self)
        self.q = queue
        self.stop_request = stop_request
        self.log = logging.getLogger(self.name)

    def run(self):
        """Inserts generated Points into the database

        https://peterman.is/blog/postgresql-bulk-insertion/2013/08/
        """
        self.log.info('Starting inserting thread %s', self.name)
        with database.get_connection() as conn:
            cur = conn.cursor()
            prepare_statement = 'PREPARE de_sim_points_plan (varchar, e_sim_point, geometry) AS ' \
                                'INSERT INTO de_sim_points (parent_geometry, point_type, geom) ' \
                                'VALUES($1, $2, ST_GeomFromWKB(ST_SetSRID($3, 900913)))'
            cur.execute(prepare_statement)

            while True:
                try:
                    sql_list = self.q.get(block=True, timeout=0.05)
                    start = time.time()
                    cur.execute('\n'.join(sql_list))
                    end = time.time()
                    del sql_list
                    self.log.info('Inserted %s, Queue remaining %s, SQL time %s',
                                  len(sql_list), self.q.qsize(), end - start)
                except Empty:
                    if self.stop_request.is_set():
                        break
                    else:
                        continue