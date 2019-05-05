#!/usr/bin/env python3

from .abstract_stat import AbstractStat


class Counter(AbstractStat):
    _type = 'counter'

    def __init__(self, default=0):
        self._default = default
        self._value = self._default

    def update(self, default=0):
        self._default = default

    def add(self, value=1.0):
        self._value = value

    def reset(self):
        self._value = self._default

    def export(self):
        return self._value
