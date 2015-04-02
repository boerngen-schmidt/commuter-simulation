import signal

import zmq


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


def signal_handler_server(signum, frame):
    logging.info('Received SIGINT. Shutting down server.')
    exit_event.set()

    # Configuration
    import configparser
    from helper.file_finder import find

    config = configparser.ConfigParser()
    config.read(find('messaging.conf'))
    section = 'client'
    conn_str = 'tcp://{host!s}:{port!s}'
    if not config.has_section(section):
        raise configparser.NoSectionError('Missing section %s' % section)

    # Socket to receive commuter to simulate
    context = zmq.Context.instance()
    receiver = context.socket(zmq.PULL)
    ''':type receiver: zmq.Socket'''
    receiver.setsockopt(zmq.RCVBUF, config.getint(section, 'pull_rcvbuf'))
    receiver.set_hwm(config.getint(section, 'pull_hwm'))
    receiver.setsockopt(zmq.LINGER, 0)
    args = dict(
        host=config.get(section, 'pull_host'),
        port=config.getint(section, 'pull_port')
    )
    receiver.connect(conn_str.format(**args))
    logging.info('Receiving messages from PUSH socket')
    count = 0
    while True:
        try:
            receiver.recv_json(zmq.NOBLOCK)
        except zmq.ZMQError:
            if count > 2:
                break
            else:
                import time
                time.sleep(2)
                count += 1
    receiver.close()
    logging.info('Done Receiving messages from PUSH socket')
    signal.signal(signal.SIGINT, default_handler)
