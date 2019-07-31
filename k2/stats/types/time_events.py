#!/usr/bin/env python3

import time

from .abstract_stat import AbstractStat


class TimeEvents(AbstractStat):
    _type = 'time_events'

    def __init__(self, limit=3600):
        self._limit = limit
        self._value = []
        self._t = 0

    def _check(self, _t):
        if _t != self._t:
            _t -= self._limit
            while self._value and self._value[0]['timestamp'] < _t:
                self._value.pop(0)
            self._t = _t

    def add(self, value):
        _t = int(time.time())
        self._value.append(
            {
                'timestamp': _t,
                'value': value,
            }
        )
        self._check(_t)

    def reset(self):
        self._t = int(time.time())
        self._value = []

    def update(self, limit):
        self._limit = limit

    def export(self):
        self._check(int(time.time()))
        return self._value

    def get_type(self):
        return self._type

    def options(self):
        d = super().options()
        d.update(
            {
                'count': len(self._value),
                'limit': self._limit,
            }
        )
        return d
