import logging
import time
from multiprocessing import Process, Event, Queue, JoinableQueue
from queue import Empty
from threading import Thread

from builder import PointType
from helper import database


class PointInsertingProcess(Process):
    """Random Sample Point inserting process

    Process reads input queue from point creator processes and generates insert batches
    for the insert threads.
    After inserting of the points is done, indexes are generated for the tables.
    """
    def __init__(self, input_queue: JoinableQueue):
        Process.__init__(self)
        self.q = input_queue
        self.thread_queue = Queue()
        self.batch_size = 5000
        self.insert_threads = 2
        self.stop_request = Event()
        self.logging = logging.getLogger(self.name)

    def set_batch_size(self, value: int):
        self.batch_size = value

    def set_insert_threads(self, value: int):
        self.insert_threads = value

    def run(self):
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

        with database.get_connection() as conn:
            with conn.cursor() as cur:
                for p in PointType:
                    self.logging.info('Creating Indexes for de_sim_points_{s}'.format((p.value, )))
                    start_index = time.time()
                    sql = "CREATE INDEX de_sim_points_{tbl!s}_parent_relation_idx " \
                          "  ON de_sim_points_{tbl!s} USING btree (parent_geometry);" \
                          "CREATE INDEX de_sim_points_{tbl!s}_geom_idx " \
                          "  ON de_sim_points_{tbl!s} USING gist (geom);"
                    cur.execute(sql.format(tbl=p.value))
                    finish_index = time.time()
                    self.logging.info('Finished creating indexes on de_sim_points_{tbl!s} in {time!r}')

    def stop(self):
        self.stop_request.set()

    def join(self, timeout=None):
        self.stop_request.set()
        super(PointInsertingProcess, self).join(timeout)


class PointInsertingThread(Thread):
    """Worker Thread for inserting Points

    Thread reads commands from queue and executes one of the pre-made execution plans.
    """
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
            prepare_statement = 'PREPARE de_sim_points_start_plan (varchar, geometry) AS ' \
                                'INSERT INTO de_sim_points_start (parent_geometry, geom) ' \
                                'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)))'
            cur.execute(prepare_statement)
            prepare_statement = 'PREPARE de_sim_points_within_start_plan (varchar, geometry) AS ' \
                                'INSERT INTO de_sim_points_within_start (parent_geometry, geom) ' \
                                'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)))'
            cur.execute(prepare_statement)
            prepare_statement = 'PREPARE de_sim_points_end_plan (varchar, geometry) AS ' \
                                'INSERT INTO de_sim_points_end (parent_geometry, geom) ' \
                                'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)))'
            cur.execute(prepare_statement)
            prepare_statement = 'PREPARE de_sim_points_within_end_plan (varchar, geometry) AS ' \
                                'INSERT INTO de_sim_points_within_end (parent_geometry, geom) ' \
                                'VALUES($1, ST_GeomFromWKB(ST_SetSRID($2, 4326)))'
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