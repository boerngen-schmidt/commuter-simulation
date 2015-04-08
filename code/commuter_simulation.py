#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The Simulation purpose is the comparison between using and not using a fuel price application.

To this purpose a simulation environment, containing of start and destination point as well as a road network and
fuel stations, was created. In this environment a commuter will be simulated driving a car from his start point to the
destination. The point in time when the car's tank will be refilled then is chosen through according to the current
strategy of the commuter, which can be either to use a fuel price application or not.

@author: Benjamin Börngen-Schmidt
"""
import argparse
import logging
import signal

from helper import logger
from helper import signal as sig


def sink(sink_args):
    import threading as t
    import simulation.sink as s

    log = logging.getLogger('SINK')

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    thread = t.Thread(target=s.sink, name='Sink')
    log.info('Started sink thread.')
    signal.signal(signal.SIGINT, sig.signal_handler)

    thread.join()
    log.info('Stopped sink thread.')


def worker(worker_args):
    import multiprocessing as mp
    from simulation.worker import CommuterSimulationZeroMQ
    number_of_processes = mp.cpu_count()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.info('Starting %d worker processes.', number_of_processes)
    processes = []
    for i in range(number_of_processes):
        processes.append(CommuterSimulationZeroMQ(sig.exit_event))
        processes[-1].name = 'P%d' % i
        processes[-1].start()

    signal.signal(signal.SIGINT, sig.signal_handler)

    for p in processes:
        p.join()
    logging.info('Worker stopped.')


def server(server_args):
    """
    The Server generates the commuters that should be simulated and makes them available to the workers over
    a ZeroMQ Push socket. The Clients can connect to the server's socket an pull the commuter.
    :return:
    """
    import simulation.server as srv
    if server_args.mode == 'first':
        srv.first_simulation()
    elif server_args.mode == 'rerun':
        srv.rerun_simulation()
    else:
        srv.first_simulation()
        srv.rerun_simulation()


if __name__ == '__main__':
    logger.setup()
    parser = argparse.ArgumentParser(description='Options for running the simulation.')
    subparsers = parser.add_subparsers(help='Choose mode of the simulation.')
    parser_client = subparsers.add_parser('worker', help='Creates a worker instance for the simulation.')
    parser_client.set_defaults(func=worker)
    parser_server = subparsers.add_parser('server', help='Creates a server instance for worker to pull data.')
    parser_server.add_argument('--mode', choices=['first', 'rerun', 'both'], help='Mode of the server.', required=True)
    parser_server.set_defaults(func=server)
    parser_sink = subparsers.add_parser('sink', help='Creates a simulation result sink instance for the simulation.')
    parser_sink.set_defaults(func=sink)
    args = parser.parse_args()
    args.func(args)