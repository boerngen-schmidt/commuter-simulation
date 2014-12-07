from enum import Enum


class MatchingType(Enum):
    within = 'Within'
    outgoing = 'Outgoing'


class PointType(Enum):
    Start = 'start'
    End = 'end'
    Within_Start = 'within_start'
    Within_End = 'within_end'