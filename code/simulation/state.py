from abc import ABCMeta, abstractmethod

__author__ = 'benjamin'


class State(metaclass=ABCMeta):
    def __init__(self):
        self.transitions = None

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def next(self, token):
        pass