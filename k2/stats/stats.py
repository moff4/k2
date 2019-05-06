#!/usr/bin/env python3

from k2.stats.types import (
    Single,
    Counter,
    Average,
    TimeEvents,
    TimeAverage,
    EventCounter,
    TimeEventCounter
)

"""
stat-name => {
    'obj': StatObject,
    'desc': description,
}
"""
Collection = {}

TypeMap = {
    'counter': Counter,
    'single': Single,
    'average': Average,
    'time_events': TimeEvents,
    'time_average': TimeAverage,
    'event_counter': EventCounter,
    'time_event_counter': TimeEventCounter,
}


def new(key, type, description=None, *a, **b):
    if type not in TypeMap:
        raise ValueError(f'unknown stat type "{type}"')
    Collection[key] = {
        'obj': TypeMap[type](*a, **b),
        'desc': description,
    }


def update(key, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key]['obj'].update(*a, **b)


def add(key, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key]['obj'].add(*a, **b)


def reset(key=None):
    if key:
        if key not in Collection:
            raise KeyError(f'stat "{key}" does not exists')
        Collection[key]['obj'].reset()
    else:
        for key in Collection:
            Collection[key]['obj'].reset()


def export_one(key):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key]['obj'].export()


def export():
    return {
        key: {
            'data': Collection[key]['obj'].export(),
            'type': Collection[key]['obj'].get_type(),
            'description': Collection[key]['desc'],
        }
        for key in Collection
    }
