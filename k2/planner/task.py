#!/usr/bin/env python3
import asyncio
import time

import k2.logger as logger
from k2.utils.autocfg import AutoCFG


class Task:
    __defaults = {
        'key': None,
        'interval': {
            'sec': 0,
            'min': 0,
            'hour': 0,
        },
        'offset': {
            'sec': 0,
            'min': 0,
            'hour': 0,
        },
        'weekdays': set(range(0, 8)),
        'args': (),
        'kwargs': {},
        'enable': True,
    }

    def __init__(self, target, **kwargs):
        if not (callable(target) or asyncio.iscoroutinefunction(target)):
            raise TypeError('target must be callable or async coroutine')
        self._cfg = AutoCFG(self.__defaults).deep_update_fields(kwargs)
        self._target = target
        self._last_run = 0
        self._missing_run = 0
        self._offset = (self._cfg.offset['hour'] * 60 + self._cfg.offset['min']) * 60 + self._cfg.offset['sec']
        self._inter = (self._cfg.interval['hour'] * 60 + self._cfg.interval['min']) * 60 + self._cfg.interval['sec']
        self._logger = logger.new_channel(f'planner_task_{self._cfg.key}', parent='planner')

    @property
    def enable(self):
        return self._cfg.enable

    @enable.setter
    def enable(self, value):
        if not isinstance(value, bool):
            raise TypeError('value must be bool')
        self._cfg.enable = value

    @property
    def delay(self):
        nr = self.next_run
        return None if nr is None else nr - time.time()

    @property
    def name(self):
        return self._cfg.key

    @property
    def next_run(self):
        _t = time.time()
        _tm = time.localtime(_t)
        if _tm.tm_wday in self._cfg.weekdays:
            nr = ((_t // self._inter) + 1) * self._inter + self._offset
            nr -= abs(_t - nr) // self._inter * self._inter
            return nr

    async def run(self, force=False, run_copy=False):
        """
            run task
        """
        self._missing_run = self._missing_run + 1 if run_copy else max(self._missing_run - 1, 0)
        _t = int(time.time())
        if (_t - self._last_run) < (self._inter / 2) or force:
            return
        self._last_run = _t
        self._logger.debug('Gonna run')
        _t = time.time()
        if asyncio.iscoroutinefunction(self._target):
            await self._target(*self._cfg.args, **self._cfg.kwargs)
        else:
            self._target(*self._cfg.args, **self._cfg.kwargs)
        self._logger.debug('Done in {:.3f} sec', time.time() - _t)
