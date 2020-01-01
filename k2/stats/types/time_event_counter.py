#!/usr/bin/env python3

import time

from .abstract_stat import AbstractStat


class TimeEventCounter(AbstractStat):
    _type = 'time_event_counter'

    def __init__(self, limit=3600):
        super().__init__()
        self._limit = limit
        self._value = {}
        self._ts = []

    def _check(self, _t):
        while self._ts and _t - self._ts[0] > self._limit:
            self._value.pop(self._ts.pop(0), None)

    def add(self):
        self._value[(_t := int(time.time()))] = self._value.get(_t, 0) + 1
        self._ts.append(_t)
        self._check(_t)

    def reset(self):
        self._value = {}

    def update(self, limit):
        self._limit = limit

    def export(self):
        self._check(int(time.time()))
        return self._value

    def get_type(self):
        return self._type

    def options(self):
        (d := super().options()).update(
            {
                'count': len(self._value),
                'limit': self._limit,
            }
        )
        return d
