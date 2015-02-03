"""
Module to capsule the distribution of commuting distances
"""
from math import floor

from builder.enums import MatchingType


commuter_distribution = {'01': (0.367, 0.196, 0.252, 0.131, 0.054),
                         '02': (0.260, 0.320, 0.341, 0.065, 0.015),
                         '03': (0.329, 0.205, 0.271, 0.145, 0.050),
                         '04': (0.316, 0.325, 0.259, 0.061, 0.039),
                         '05': (0.310, 0.229, 0.282, 0.135, 0.044),
                         '06': (0.288, 0.199, 0.304, 0.158, 0.052),
                         '07': (0.303, 0.185, 0.285, 0.163, 0.065),
                         '08': (0.338, 0.212, 0.297, 0.118, 0.035),
                         '09': (0.321, 0.194, 0.300, 0.134, 0.051),
                         '10': (0.243, 0.209, 0.332, 0.171, 0.045),
                         '11': (0.224, 0.303, 0.372, 0.084, 0.017),
                         '12': (0.301, 0.160, 0.255, 0.209, 0.075),
                         '13': (0.348, 0.184, 0.235, 0.147, 0.087),
                         '14': (0.338, 0.239, 0.276, 0.108, 0.039),
                         '15': (0.334, 0.205, 0.254, 0.136, 0.070),
                         '16': (0.367, 0.196, 0.252, 0.131, 0.054)}

commuting_distance = ({'min_d': 2000, 'max_d': 5000},
                      {'min_d': 5000, 'max_d': 10000},
                      {'min_d': 10000, 'max_d': 25000},
                      {'min_d': 25000, 'max_d': 50000},
                      {'min_d': 50000, 'max_d': 140000})

delta_commuters = 0.1


class MatchingDistributionRevised(object):
    def __init__(self, rs: str, commuters: int, matching_type: MatchingType, min_distance, max_distance):
        self._rs = rs
        self._commuters = commuters
        self._type = matching_type
        self._max_d = max_distance
        self._min_d = min_distance

    @property
    def rs(self) -> str:
        return self._rs

    @property
    def commuter(self) -> int:
        return self._commuters

    @property
    def max_d(self):
        return self._max_d

    @property
    def min_d(self):
        return self._min_d
    @property
    def matching_type(self) -> MatchingType:
        return self._type


class MatchingDistributionLookup(object):
    def __init__(self, rs, outgoing, within):
        self._rs = rs
        self._within = within
        self._outgoing = outgoing

    @property
    def rs(self):
        return self._rs

    @property
    def within(self):
        return self._within

    @property
    def outgoing(self):
        return self._outgoing


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
