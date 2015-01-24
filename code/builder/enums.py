from enum import Enum


__author__ = 'benjamin'


class PointType(Enum):
    Start = 'start'
    End = 'end'
    Within_Start = 'within_start'
    Within_End = 'within_end'


class MatchingType(Enum):
    within = 'Within'
    outgoing = 'Outgoing'
