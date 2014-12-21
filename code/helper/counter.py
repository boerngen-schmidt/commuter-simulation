__author__ = 'benjamin'

from multiprocessing import Value


class Counter(object):
    def __init__(self, maximum):
        self.max = Value('i', maximum)
        self.val = Value('i', 0)

    def increment_both(self):
        with self.max.get_lock():
            self.max.value += 1
        return self.increment()

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
        return self.max.value
