#!/usr/bin/env python3

from .abstract_stat import AbstractStat


class Single(AbstractStat):
    _type = 'single'

    def __init__(self):
        self._value = None

    def add(self, value):
        self._value = value

    def reset(self):
        self._value = None

    def export(self):
        return self._value
