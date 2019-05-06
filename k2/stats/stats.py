#!/usr/bin/env python3
import asyncio

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

async def __callback(event, key, *a, **b):
    if Collection[key]['callback'] is not None:
        if callable(Collection[key]['callback']):
            Collection[key]['callback'](event, key, *a, **b)
        else:
            await Collection[key]['callback'](event, key, *a, **b)


def new(key, type, description=None, callback=None, *a, **b):
    if type not in TypeMap:
        raise ValueError(f'unknown stat type "{type}"')
    Collection[key] = {
        'obj': TypeMap[type](*a, **b),
        'desc': description,
        'callback': callback,
    }


def update(key, description=None, callback=None, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    if description is not None:
        Collection[key]['desc'] = description
    if callable is not None:
        if callable(callback) or asyncio.iscoroutinefunction(callback):
            Collection[key]['callback'] = callback
        else:
            raise TypeError('callback must be callable or asyncio.coroutine')
    Collection[key]['obj'].update(*a, **b)


async def add(key, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key]['obj'].add(*a, **b)
    await __callback('add', key, *a, **b)


async def reset(key=None):
    if key:
        if key not in Collection:
            raise KeyError(f'stat "{key}" does not exists')
        Collection[key]['obj'].reset()
        await __callback('reset', key)
    else:
        for key in Collection:
            Collection[key]['obj'].reset()
            await __callback('reset', key)


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
