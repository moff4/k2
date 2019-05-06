#!/usr/bin/env python3

import time

from .abstract_stat import AbstractStat


class TimeEventCounter(AbstractStat):
    _type = 'time_event_counter'

    def __init__(self, limit=3600):
        self._limit = limit
        self._value = {}
        self._t = 0

    def _check(self, _t):
        if _t != self._t:
            _t -= self._limit
            self._value = {k: self._value[k] for k in self._value if k > _t}
            self._t = _t

    def add(self):
        _t = int(time.time())
        self._value[_t] = self._value.get(_t, 0) + 1
        self._check(_t)

    def reset(self):
        self._t = int(time.time())
        self._value = {}

    def update(self, limit):
        self._limit = limit

    def export(self):
        self._check(int(time.time()))
        return self._value

    def get_type(self):
        return self._type
