#!/usr/bin/env python3

from .abstract_stat import AbstractStat


class Average(AbstractStat):
    _type = 'average'

    def __init__(self, limit=500):
        self._limit = limit
        self._value = []

    def update(self, limit=500):
        self._limit = limit

    def add(self, value):
        self._value.append(value)
        while len(self._value) > self._limit:
            self._value.pop(0)

    def reset(self):
        self._value = []

    def export(self):
        return sum(self._value) / len(self._value)

    def options(self):
        d = super().options()
        d.update(
            {
                'count': len(self._value),
                'limit': self._limit,
            }
        )
        return d