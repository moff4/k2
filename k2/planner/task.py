#!/usr/bin/env python3
import asyncio
import time

import k2.logger as logger
from k2.utils.autocfg import AutoCFG

SHEDULE_LIMIT = 100


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
        'count': None,
        'args': (),
        'kwargs': {},
        'enable': True,
    }

    def __init__(self, target, **kwargs):
        if not (callable(target) or asyncio.iscoroutinefunction(target)):
            raise TypeError('target must be callable or async coroutine')
        self._cfg = AutoCFG(self.__defaults).deep_update_fields(kwargs)
        self._target = target
        self._offset = (self._cfg.offset['hour'] * 60 + self._cfg.offset['min']) * 60 + self._cfg.offset['sec']
        self._inter = (self._cfg.interval['hour'] * 60 + self._cfg.interval['min']) * 60 + self._cfg.interval['sec']
        self.logger = logger.new_channel('planner_task_{}'.format(self._cfg.key), parent='planner')
        self._shedule = []

    def _generate_shedule(self):
        if not self.enable:
            return

        self._shedule = []
        _t = time.time()
        nr = ((_t // self._inter) + 1) * self._inter + self._offset
        while len(self._shedule) < SHEDULE_LIMIT and (nr - _t) < 7 * 3600:
            if time.localtime(nr).tm_wday in self._cfg.weekdays:
                self._shedule.append(nr)
            nr += self._inter

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
        if not self._shedule:
            self._generate_shedule()
        if self._shedule:
            return self._shedule[0]

    def prepare_for_run(self, run_copy=False):
        if self._shedule and not run_copy:
            self._shedule.pop(0)

    async def run(self, run_copy=False):
        """
            run task
            do not call task directlly
            only throught planner
        """
        await self.logger.debug('Gonna run')
        _t = time.time()
        try:
            if asyncio.iscoroutinefunction(self._target):
                await self._target(*self._cfg.args, **self._cfg.kwargs)
            else:
                self._target(*self._cfg.args, **self._cfg.kwargs)
        except Exception:
            await self.logger.exception('Task "{}" failed', self._cfg.key)
        else:
            await self.logger.debug('Done in {:.3f} sec', time.time() - _t)
