__author__ = 'Benjamin'

from .core import Transition

class DriveToHome(Transition):
    pass
class DriveToWork(Transition):
    pass
class DriveToFillingStation(Transition):
    pass
class ArriveAtHome(Transition):
    pass
class ArriveAtWork(Transition):
    pass
class ArriveAtFillingStation(Transition):
    pass
class SearchFillingStation(Transition):
    pass
class Start(Transition):
    pass
class End(Transition):
    pass

