#!/usr/bin/env python3

import time

from .average import Average


class TimeAverage(Average):
    _type = 'time_average'

    def add(self, value):
        _t = time.time()
        self._value.append((_t, value))
        _t -= self._limit
        while self._value and self._value[0][0] < _t:
            self._value.pop(0)

    def export(self):
        return sum(j for i, j in self._value) / len(self._value)
