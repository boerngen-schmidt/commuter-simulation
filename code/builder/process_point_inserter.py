import logging
import time
from multiprocessing import Process, Event, Queue, JoinableQueue
from queue import Empty
from threading import Thread

from helper import database


class PointInsertingProcess(Process):
    """Random Sample Point inserting process

    Process reads input queue from point creator processes and generates insert batches
    for the insert threads.
    After inserting of the points is done, indexes are generated for the tables.
    """

    def __init__(self, input_queue: JoinableQueue, plans):
        Process.__init__(self)
        self.q = input_queue
        self.thread_queue = Queue()
        self.batch_size = 5000
        self.insert_threads = 2
        self.stop_request = Event()
        self.logging = logging.getLogger(self.name)
        self.plans = plans

    def set_batch_size(self, value: int):
        self.batch_size = value

    def set_insert_threads(self, value: int):
        self.insert_threads = value

    def run(self):
        threads = []
        for i in range(self.insert_threads):
            name = 'Inserting Thread %s' % i
            t = PointInsertingThread(self.thread_queue, self.stop_request, self.plans)
            t.setName(name)
            threads.append(t)
            t.start()

        sql_commands = []
        while True:
            try:
                sql_commands.append(self.q.get(block=True, timeout=0.5))
            except Empty:
                # Nothing there yet. Wait for data again.
                continue
            else:
                if len(sql_commands) >= self.batch_size:
                    self.thread_queue.put(sql_commands)
                    sql_commands = []
                self.q.task_done()
            finally:
                if self.stop_request.is_set():
                    self.logging.info('Recieved stop event. Queue size %s, SQL commands %s',
                                      self.q.qsize(), len(sql_commands))
                    while not self.q.empty():
                        sql_commands.append(self.q.get())
                        self.q.task_done()
                    self.thread_queue.put(sql_commands)

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
    """Worker Thread for inserting Points

    Thread reads commands from queue and executes one of the pre-made execution plans.
    """

    def __init__(self, queue: Queue, stop_request: Event, plans):
        Thread.__init__(self)
        self.q = queue
        self.stop_request = stop_request
        self.log = logging.getLogger(self.name)
        self.plans = plans

    def run(self):
        """Inserts generated Points into the database

        https://peterman.is/blog/postgresql-bulk-insertion/2013/08/
        """
        self.log.info('Starting inserting thread %s', self.name)
        with database.get_connection() as conn:
            cur = conn.cursor()
            for prepare_statement in self.plans:
                cur.execute(prepare_statement)
            conn.commit()

            while True:
                try:
                    sql_list = self.q.get(block=True, timeout=0.05)
                    start = time.time()
                    cur.execute('\n'.join(sql_list))
                    conn.commit()
                    end = time.time()
                    self.log.info('Inserted %s, Queue remaining %s, SQL time %s',
                                  len(sql_list), self.q.qsize(), end - start)
                    del sql_list
                except Empty:
                    if self.stop_request.is_set():
                        break
                    else:
                        continue


class PointInsertIndexingThread(Thread):
    def __init__(self, table):
        Thread.__init__(self)
        self.tbl = table
        self.logging = logging.getLogger(self.name)

    def run(self):
        self.logging.info('Start creating Indexes for de_sim_points_%s tables', self.tbl)
        with database.get_connection() as conn:
            cur = conn.cursor()
            start_index = time.time()
            sql = "ALTER TABLE de_sim_points_{tbl!s} SET (FILLFACTOR=100); " \
                  "CREATE INDEX de_sim_points_{tbl!s}_parent_relation_idx " \
                  "  ON de_sim_points_{tbl!s} USING btree (parent_geometry) WITH (FILLFACTOR=100); " \
                  "CREATE INDEX de_sim_points_{tbl!s}_geom_idx " \
                  "  ON de_sim_points_{tbl!s} USING gist (geom) WITH (FILLFACTOR=100); " \
                  "CREATE INDEX de_sim_points_{tbl!s}_used_idx ON de_sim_points_{tbl!s} (used ASC NULLS LAST) WITH (FILLFACTOR=100);" \
                  "ALTER TABLE de_sim_points_{tbl!s} CLUSTER ON de_sim_points_{tbl!s}_geom_idx; "
            cur.execute(sql.format(tbl=self.tbl))
            conn.commit()
            conn.set_isolation_level(0)
            cur.execute('VACUUM ANALYSE de_sim_points_{tbl!s}'.format(tbl=self.tbl))
            conn.commit()
            finish_index = time.time()
            self.logging.info('Finished creating indexes on de_sim_points_%s in %s',
                              self.tbl, (finish_index - start_index))