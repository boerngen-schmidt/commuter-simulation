"""
Module for information about routes

@author: Benjamin Börngen-Schmidt
"""
from enum import Enum

from simulation.event import Event


class Route(object):
    """Route for a commuter

    The Route class encapsulates the route fragments and makes the route itself iterable.
    """
    def __init__(self, start, destination, fragments, event: Event, geom_line, distance):
        self._fragments = fragments
        self._index = 0
        self._start = start
        self._dest = destination
        self._event = event
        self._line = geom_line
        self._distance = distance

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._fragments):
            self._index = 0     # reset the index, so the route could be automatically reused
            raise StopIteration
        else:
            self._index += 1
            return self._fragments[self._index-1]

    def reset(self):
        self._index = 0

    @property
    def event_type(self):
        return self._event

    @property
    def start(self):
        return self._start

    @property
    def destination(self):
        return self._dest

    @property
    def geom_line(self):
        return self._line

    @property
    def distance(self):
        return self._distance


class RouteFragment(object):
    """Represents a Fragment of the Route"""
    def __init__(self, fragment_id, source, target, speed, distance, clazz):
        """Constructor"""
        # Check Parameters
        if speed <= 0:
            raise ValueError('Value of speed cannot be zero or negative')

        if distance <= 0:
            raise ValueError('Value of distance cannot be zero or negative')

        '''Class attributes'''
        self._fragment_id = fragment_id
        self._speed = speed              # km/h
        self._distance = distance        # km
        self._time = int(round(self._distance / self._speed * 60 * 60))
        self._clazz = RouteClazz(clazz)
        self._source = source
        self._target = target

    @property
    def travel_time(self):
        """Returns the time needed to drive the fragment

        :rtype: int Time in seconds
        """
        return self._time

    @property
    def length(self):
        """Length of route segment in km"""
        return self._distance

    @property
    def speed_limit(self):
        return self._speed

    @property
    def road_type(self):
        """Type of road"""
        return self._clazz

    @property
    def target(self):
        return self._target

    @property
    def source(self):
        return self._source


class RouteClazz(Enum):
    motorway =  11
    motorway_link =  12
    trunk =          13
    trunk_link =     14
    primary =        15
    primary_link =   16
    secondary =      21
    secondary_link = 22
    tertiary =       31
    tertiary_link =  32
    residential =    41
    road =           42
    unclassified =   43
    service =        51
    living_street =  63