#!/usr/bin/env python3

import time

from .average import Average


class TimeAverage(Average):
    _type = 'time_average'

    def add(self, value):
        self._value.append((_t := time.time(), value))
        _t -= self._limit
        while self._value and self._value[0][0] < _t:
            self._value.pop(0)

    def export(self):
        return sum(j for _, j in self._value) / len(self._value)
