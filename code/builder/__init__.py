from enum import Enum


class MatchingType(Enum):
    within = 0
    outgoing = 1


class PointType(Enum):
    Start = 'start'
    End = 'end'
    Within_Start = 'within_start'
    Within_End = 'within_end'