import logging
import time
from multiprocessing import Process, Event
from queue import Empty
from threading import Thread
from queue import Queue as ThreadQueue

from database import connection


class PointInsertingProcess(Process):
    """Random Sample Point inserting process

    Process reads input queue from point creator processes and generates insert batches
    for the insert threads.
    After inserting of the points is done, indexes are generated for the tables.
    """

    def __init__(self, input_queue, plans, exit_event):
        """

        :param input_queue:
        :type input_queue: multiprocessing.Queue
        :param plans:
        :param exit_event:
        :return:
        """
        super().__init__()
        self.q = input_queue
        self.thread_queue = ThreadQueue()
        self.batch_size = 5000
        self.insert_threads = 1
        self.exit_event = exit_event
        self.stop_request = Event()
        self.logging = logging.getLogger(self.name)
        self.plans = plans

    def __del__(self):
        if self.exit_event.is_set():
            self.logging.warn('Cleaning %d elements from Queue ... ', self.q.qsize())
            while not self.q.empty():
                self.q.get()

    def set_batch_size(self, value: int):
        self.batch_size = value

    def set_insert_threads(self, value: int):
        self.insert_threads = value

    def _start_threads(self, amount):
        threads = []
        for i in range(amount):
            name = 'Inserting Thread'
            t = PointInsertingThread(self.thread_queue, self.stop_request, self.plans)
            t.setName(name)
            threads.append(t)
            t.start()
        return threads

    def run(self):
        threads = self._start_threads(self.insert_threads)

        sql_commands = []
        while True:
            try:
                sql_commands.append(self.q.get(timeout=0.5))
            except Empty:
                if self.exit_event.is_set():
                    break
                continue
            else:
                if len(sql_commands) >= self.batch_size:
                    self.thread_queue.put(sql_commands)
                    sql_commands = []
            finally:
                if self.stop_request.is_set():
                    break

        threads += self._start_threads(5)
        # Flush Queue to sql commands
        while not self.q.empty():
            sql_commands.append(self.q.get())
        self.thread_queue.put(sql_commands)
        self.thread_queue.join()
        self.stop_request.set()
        for t in threads:
            t.join()


class PointInsertingThread(Thread):
    """Worker Thread for inserting Points

    Thread reads commands from queue and executes one of the pre-made execution plans.
    """
    def __init__(self, queue, stop_request, plans):
        """Thread initialization

        :param queue: Queue with SQL commands
        :type queue: queue.Queue
        :param stop_request: Event to stop the thread during operation
        :type stop_request: multiprocessing.Event
        :param plans: The insert plans
        """
        Thread.__init__(self)
        self.q = queue
        self.stop_request = stop_request
        self.log = logging.getLogger(self.__class__.__name__)
        self.plans = plans

    def run(self):
        """Inserts generated Points into the database

        Inspired by https://peterman.is/blog/postgresql-bulk-insertion/2013/08/
        """
        self.log.info('Starting inserting thread %s', self.name)
        with connection.get_connection() as conn:
            cur = conn.cursor()
            for prepare_statement in self.plans:
                cur.execute(prepare_statement)
            conn.commit()

            while True:
                try:
                    sql_list = self.q.get(timeout=0.05)
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
                    continue
                else:
                    self.q.task_done()

            # TODO remove after test?!
            self.log.warn('Cleaning %d elements from Queue ... ', self.q.qsize())
            while not self.q.empty():
                self.q.get()
                self.q.task_done()
