#!/usr/bin/env python3


class AbstractStat:
    """
        Abstract Stat Type
        Inherite and overwrite all methods
    """
    _type = 'abstract'

    def __init__(self, *a, **b):
        pass

    def update(self, *a, **b):
        pass

    def add(self, *a, **b):
        pass

    def reset(self, *a, **b):
        pass

    def export(self):
        pass

    def get_type(self):
        return self._type
