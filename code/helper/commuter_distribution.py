"""
Module to capsule the distribution of commuting distances
"""
from multiprocessing import Lock

from builder import MatchingType
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


class MatchingDistribution():
    def __init__(self, rs):
        self._rs = rs
        self._cur_within_idx = 0
        self._cur_outgoing_idx = 0
        self._cur_within_idx_lock = Lock()
        self._cur_outgoing_idx_lock = Lock()

        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT outgoing, within FROM de_commuter WHERE rs = %s', (rs, ))
            conn.commit()
            (self.outgoing, self.within) = cur.fetchone()

        self._dist_within = [self.within*p for p in commuter_distribution[self._rs[:2]]]
        self._count_within = [0] * len(commuter_distribution[self._rs[:2]])
        self._count_within_lock = Lock()

        self._dist_outgoing = [self.outgoing*p for p in commuter_distribution[self._rs[:2]]]
        self._count_outgoing = [0] * len(commuter_distribution[self._rs[:2]])
        self._count_outgoing_lock = Lock()

        self.commuting_distance = ({'min_d':  2000, 'max_d': 10000},
                                   {'min_d': 10000, 'max_d': 25000},
                                   {'min_d': 25000, 'max_d': 50000},
                                   {'min_d': 50000, 'max_d': 140000})

    def get_distance(self, match_type: MatchingType, index):
        if match_type is MatchingType.within:
            self._cur_within_idx_lock.acquire()
            result = self._cur_within_idx
            self._count_within_lock.release()
        else:
            self._cur_outgoing_idx_lock.acquire()
            result = self._cur_outgoing_idx
            self._cur_outgoing_idx_lock.release()
        return self.commuting_distance[result]

    @property
    def within_idx(self):
        self._cur_within_idx_lock.acquire()
        if self._count_within[self._cur_within_idx] >= self._dist_within[self._cur_within_idx]:
            self._cur_within_idx += 1
        result = self._cur_within_idx
        self._cur_within_idx_lock.release()
        return result

    @property
    def outgoing_idx(self):
        self._cur_outgoing_idx_lock.acquire()
        if self._count_outgoing[self._cur_outgoing_idx] >= self._dist_outgoing[self._cur_outgoing_idx]:
            self._cur_outgoing_idx +=1
        result = self._cur_outgoing_idx
        self._cur_outgoing_idx_lock.release()
        return result

    def increase(self, matching_type: MatchingType, index):
        if MatchingType.outgoing is matching_type:
            return self.increase_outgoing()
        else:
            return self.increase_within()

    def increase_within(self, index):
        """
        Tries to increase the count for the within distribution

        :param index: Index of the corresponding category for which start and end point where searched
        :rtype: bool
        :return: True indicates that increment was successful,
                 False that it wasn't due to already enough commuters distributed in category
        """
        self._count_within_lock.acquire()
        if self._count_within[index] >= self._dist_within[index]:
            self._count_within_lock.release()
            return False
        else:
            self._count_within[index] += 1
            self._count_within_lock.release()
            return True

    def increase_outgoing(self, index):
        """
        Tries to increase the count for the outgoing distribution

        :param index: Index of the corresponding category for which start and end point where searched
        :rtype: bool
        :return: True indicates that increment was successful,
                 False that it wasn't due to already enough commuters distributed in category
        """
        self._count_outgoing_lock.acquire()
        if self._count_outgoing[index] >= self._dist_outgoing[index]:
            self._count_outgoing_lock.release()
            return False
        else:
            self._count_outgoing[index] += 1
            self._count_outgoing_lock.release()
            return True

