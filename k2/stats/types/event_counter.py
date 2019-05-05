#!/usr/bin/env python3

from collections import Counter

from .abstract_stat import AbstractStat


class EventCounter(AbstractStat):
    _type = 'event_counter'

    def __init__(self):
        self._value = Counter()

    def add(self, key):
        self._value[key] += 1

    def reset(self, key=None):
        if key is None:
            self._value = Counter()
        else:
            self._value[key] = 0

    def export(self):
        return dict(self._value)

    def get_type(self):
        return self._type
