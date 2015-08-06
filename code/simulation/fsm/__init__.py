from enum import Enum

from .core import SimulationFSM


class Transitions(Enum):
    DriveToHome = 'drive_to_home'
    DriveToWork = 'drive_to_work'
    DriveToFillingStation = 'drive_to_filling_station'
    ArriveAtHome = 'arrived_at_home'
    ArriveAtWork = 'arrived_at_work'
    ArriveAtFillingStation = 'arrived_at_filling_station'
    SearchFillingStation = 'search_filling_station'
    Start = 'commuter_wakes_up_at_home'
    End = 'commuter_is_done'


class States(Enum):
    Start = 'Start'
    End = 'End'
    Home = 'Home'
    Work = 'Work'
    FillingStation = 'FillingStation'
    SearchFillingStation = 'SearchFillingStation'
    Drive = 'Drive'


class UnknownTransitionCondition(Exception):
    pass

