#!/usr/bin/env python3

from k2.stats.types import (
    Single,
    Counter,
    Average,
    TimeAverage,
    EventCounter,
    TimeEventCounter
)

# stat-name -> StatObject
Collection = {}

TypeMap = {
    'event_counter': EventCounter,
    'counter': Counter,
    'single': Single,
    'average': Average,
    'time_average': TimeAverage,
}


def new(key, type, *a, **b):
    if type not in TypeMap:
        raise ValueError(f'unknown stat type "{type}"')
    Collection[key] = TypeMap[type](*a, **b)


def update(key, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key].update(*a, **b)


def add(key, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key].add(*a, **b)


def reset(key):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key].reset()


def export_one(key):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key].export()


def export():
    return {
        key: {
            'data': Collection[key].export(),
            'type': Collection[key].get_type(),
        }
        for key in Collection
    }
