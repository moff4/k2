#!/usr/bin/env python3
import asyncio
from dataclasses import dataclass
from typing import Dict, Callable, Optional

from k2.stats.types import (
    Single,
    Counter,
    Average,
    TimeEvents,
    TimeAverage,
    AbstractStat,
    EventCounter,
    TimeEventCounter
)

"""
stat-name => {
    'obj': StatObject,
    'desc': description,
}
"""


@dataclass
class Stat:
    obj: AbstractStat
    desc: Optional[str] = None
    callback: Optional[Callable] = None


Collection = {}  # type: Dict[str, Stat]

STATS_TYPE_COUNTER = Counter._type
STATS_TYPE_SINGLE = Single._type
STATS_TYPE_AVERAGE = Average._type
STATS_TYPE_TIMEEVENTS = TimeEvents._type
STATS_TYPE_TIMEAVERAGE = TimeAverage._type
STATS_TYPE_EVENTCOUNTER = EventCounter._type
STATS_TYPE_TIMEEVENTCOUNTER = TimeEventCounter._type

TypeMap = {
    STATS_TYPE_COUNTER: Counter,
    STATS_TYPE_SINGLE: Single,
    STATS_TYPE_AVERAGE: Average,
    STATS_TYPE_TIMEEVENTS: TimeEvents,
    STATS_TYPE_TIMEAVERAGE: TimeAverage,
    STATS_TYPE_EVENTCOUNTER: EventCounter,
    STATS_TYPE_TIMEEVENTCOUNTER: TimeEventCounter,
}


async def __callback(event: str, key: str, *a, **b):
    callback = Collection[key].callback
    if callback:
        if callable(callback):
            callback(event, key, *a, **b)
        else:
            await callback(event, key, *a, **b)


def new(key: str, type: str, description: str=None, callback: Callable=None, *a, **b):
    if type not in TypeMap:
        raise ValueError(f'unknown stat type "{type}"')
    if callback is not None:
        if not callable(callback) and not asyncio.iscoroutinefunction(callback):
            raise TypeError('callback must be callable or asyncio.coroutine')
    Collection[key] = Stat(
        obj=TypeMap[type](*a, **b),
        desc=description,
        callback=callback,
    )


def update(key: str, description: str=None, callback=None, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    if description is not None:
        Collection[key].desc = description
    if callable:
        if callable(callback) or asyncio.iscoroutinefunction(callback):
            Collection[key].callback = callback
        else:
            raise TypeError('callback must be callable or asyncio.coroutine')
    Collection[key].obj.update(*a, **b)


async def add(key: str, *a, **b):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    Collection[key].obj.add(*a, **b)
    await __callback('add', key, *a, **b)


async def reset(key: str=None):
    if key:
        if key not in Collection:
            raise KeyError(f'stat "{key}" does not exists')
        Collection[key].obj.reset()
        await __callback('reset', key)
    else:
        for key in Collection:
            Collection[key].obj.reset()
            await __callback('reset', key)


def __do_export(key: str):
    obj = Collection[key].obj
    return {
        'data': obj.options(),
        'type': obj.get_type(),
        'description': Collection[key].desc,
    }


def export_one(key: str):
    if key not in Collection:
        raise KeyError(f'stat "{key}" does not exists')
    return __do_export(key)


def export():
    return {
        key: __do_export(key)
        for key in Collection
    }
