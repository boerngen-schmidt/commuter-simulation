"""
Module to capsule the distribution of commuting distances
"""
from math import floor

from matching import MatchingType


commuter_distribution = {'01': (0.5, 0.28, 0.17, 0.05),
                         '02': (0.5, 0.28, 0.17, 0.05),
                         '03': (0.5, 0.28, 0.17, 0.05),
                         '04': (0.5, 0.28, 0.17, 0.05),
                         '05': (0.5, 0.28, 0.17, 0.05),
                         '06': (0.5, 0.28, 0.17, 0.05),
                         '07': (0.5, 0.28, 0.17, 0.05),
                         '08': (0.5, 0.28, 0.17, 0.05),
                         '09': (0.5, 0.28, 0.17, 0.05),
                         '10': (0.5, 0.28, 0.17, 0.05),
                         '11': (0.5, 0.28, 0.17, 0.05),
                         '12': (0.5, 0.28, 0.17, 0.05),
                         '13': (0.5, 0.28, 0.17, 0.05),
                         '14': (0.5, 0.28, 0.17, 0.05),
                         '15': (0.5, 0.28, 0.17, 0.05),
                         '16': (0.5, 0.28, 0.17, 0.05)}

commuting_distance = ({'min_d': 2000, 'max_d': 10000},
                      {'min_d': 10000, 'max_d': 25000},
                      {'min_d': 25000, 'max_d': 50000},
                      {'min_d': 50000, 'max_d': 140000})

delta_commuters = 0.1


class MatchingDistribution(object):
    __slots__ = ['_rs', '_index', '_data', '_age']

    def __init__(self, rs, within, outgoing):
        self._rs = rs
        self._index = 0
        self._age = 0
        self.__build_data(within, self.__build_outgoing_distribution(outgoing))

    def reuse(self, within, outgoing):
        """
        Makes the MatchingDistribution reusable

        :param within: Int with the remaining commuters within to match
        :param outgoing: List of int with remaining outgoing commuters to match

        """
        if outgoing is int:
            outgoing = self.__build_outgoing_distribution(outgoing)
        self.__build_data(within, outgoing)
        self._index = 0
        self._age += 1

    def __build_outgoing_distribution(self, amount_outgoing):
        N = len(commuter_distribution[self._rs[:2]])
        return [int(floor(amount_outgoing * commuter_distribution[self._rs[:2]][i])) for i in range(N)]

    def __build_data(self, within, outgoing):
        self._data = [{'commuters': within, 'type': MatchingType.within, 'rs': self._rs, 'min_d': 2000, 'max_d': -1}]
        for i, o in zip(range(len(outgoing)), outgoing):
            self._data.append(
                dict({'commuters': o, 'type': MatchingType.outgoing, 'rs': self._rs}, **commuting_distance[i]))

    @property
    def age(self):
        return self._age

    @property
    def rs(self):
        return self._rs

    @property
    def index(self):
        return self._index

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def __len__(self):
        return len(list(zip(commuting_distance, commuter_distribution[self._rs[:2]])))

    @property
    def data(self):
        return self._data

    def next(self):
        if self._index < len(self._data):
            result = self._data[self._index]
            self._index += 1
            return result
        else:
            raise StopIteration()

    def has_next(self):
        return self._index + 1 < len(self._data)
