from contextlib import contextmanager
import logging
import multiprocessing

from database.process_point_inserter import PointInsertingProcess


exit_event = multiprocessing.Event()


def signal_handler(signum, frame):
    '''
    Signal Handler for CTRL + C (SIGINT)

    Sets an exit event, which is passed to the processes, to true.
    :param signum: Number of the signal
    :param frame: Python frame
    '''
    logging.info('Received SIGINT. Exiting processes')
    exit_event.set()


@contextmanager
def inserting_process(insert_queue, plans, threads=2, batch_size=5000):
    """Generator for inserting process

    :param multiprocessing.Queue insert_queue: Queue for to be inserted Objects
    """
    insert_process = PointInsertingProcess(insert_queue, plans)
    insert_process.set_batch_size(batch_size)
    insert_process.set_insert_threads(threads)
    insert_process.start()
    yield
    insert_process.join()