from enum import Enum

__author__ = 'benjamin'


class Event(Enum):
    ArrivedAtWork = 1
    ArrivedAtHome = 2
    ReserveTank = 3
    FinishedWork = 4
    LeavingHome = 5
    FillingStation = 6


class SimEvent(object):
    def __init__(self, event_type: Event, data: dict={}):
        self._event_type = event_type
        self._data = data
        if not self._check_data():
            raise AttributeError('Missing Attributes for Event: "%s"' % event_type.name)

    @property
    def data(self) -> dict:
        return self._data

    @property
    def type(self) -> Event:
        return self._event_type

    def _check_data(self):
        keys = self._data.keys()
        e = self._event_type
        if e is Event.ArrivedAtHome or e is Event.ArrivedAtWork:
            return keys in ['time_driven']
        elif e is Event.ReserveTank:
            return keys in ['route_start', 'route_destination', 'current_position', 'time_driven', 'route_event']
        elif e is Event.FillingStation:
            return keys in ['time_driven', 'current_position', 'route_destination','route_event']
        else:
            return False