"""
Module to capsule the distribution of commuting distances
"""
from math import floor

from helper import database


# Could be placed in the database, but for now we keep it static
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


commuting_distance = ({'min_d':  2000, 'max_d': 10000},
                      {'min_d': 10000, 'max_d': 25000},
                      {'min_d': 25000, 'max_d': 50000},
                      {'min_d': 50000, 'max_d': 140000})


class MatchingDistribution(object):
    __slots__ = ['_rs', '_index', '_data', '_dist_within', '_dist_outgoing']

    def __init__(self, rs):
        self._rs = rs
        self._index = 0
        self._data = {}

        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT outgoing, within FROM de_commuter WHERE rs = %s', (rs, ))
            conn.commit()
            (outgoing, within) = cur.fetchone()

        self._dist_within = [int(floor(within*p)) for p in commuter_distribution[self._rs[:2]]]
        self._dist_outgoing = [int(floor(outgoing*p)) for p in commuter_distribution[self._rs[:2]]]

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

    @property
    def commuter_within(self):
        return self._data['within']['commuters']

    @property
    def commuter_outgoing(self):
        return self._data['outgoing']['commuters']

    def next(self):
        if self._index < len(list(zip(commuting_distance, commuter_distribution[self._rs[:2]]))):
            self._data = {
                'within': dict({'commuters': self._dist_within[self._index]}, **commuting_distance[self._index]),
                'outgoing': dict({'commuters': self._dist_outgoing[self._index]}, **commuting_distance[self._index])
            }
            self._index += 1
            return self._data
        else:
            raise StopIteration()

    def has_next(self):
        return self._index+1 < len(list(zip(commuting_distance, commuter_distribution[self._rs[:2]])))