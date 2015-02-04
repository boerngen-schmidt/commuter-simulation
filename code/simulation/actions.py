from enum import Enum


class CommuterActions(Enum):
    ArrivedAtWork = 10
    ArrivedAtHome = 11
    DriveToWork = 20
    DriveHome = 21
    RefillCar = 30
    LeavingFillingStation = 31
    FillingStation = 32
    FinishedWork = 40
    LeavingHome = 41