import signal

__author__ = 'benjamin'

import logging
import multiprocessing


exit_event = multiprocessing.Event()
default_handler = signal.getsignal(signal.SIGINT)

def signal_handler(signum, frame):
    '''
    Signal Handler for CTRL + C (SIGINT)

    Sets an exit event, which is passed to the processes, to true.
    :param signum: Number of the signal
    :param frame: Python frame
    '''
    logging.info('Received SIGINT. Exiting processes')
    exit_event.set()
    signal.signal(signal.SIGINT, default_handler)
