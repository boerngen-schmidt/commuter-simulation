__author__ = 'benjamin'

from multiprocessing import Value


class Counter(object):
    def __init__(self, maximum):
        self.max = maximum
        self.val = Value('i', 0)

    def increment(self, n=1):
        with self.val.get_lock():
            self.val.value += n
            result = self.value
        return result

    @property
    def value(self):
        return self.val.value

    @property
    def maximum(self):
        return self.max
