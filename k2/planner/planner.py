#!/usr/bin/env python3
import os
import asyncio
import time
from collections import defaultdict

import k2.logger as logger
from k2.planner.task import Task
from k2.utils.autocfg import AutoCFG


class Planner:
    """
        cron service
    """

    __defaults = {
        'timeout': 5.0,
        'loop': None
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG(self.__defaults).update_fields(kwargs)
        self.RUN = True
        self.task = None
        if self.cfg.loop is None:
            self.cfg.loop = asyncio.get_event_loop()
        self._tasks = {}
        self._running_tasks = []
        self._logger = logger.new_channel(
            key='planner',
            parent=logger.get_channel('base_logger'),
        )

    @property
    def shedule(self):
        """
            return shedule for all tasks
            as list of tuples(task-name, timestamp)
        """
        shedule = []
        for key, task in self._tasks.items():
            shedule.extend(((key, ts) for ts in task.shedule))
        return sorted(shedule, key=lambda x: x[1])

    @shedule.setter
    def shedule(self, shedule):
        """
            takes list of tuples as shedule for all tasks
            and upd each task shedules
        """
        ss = defaultdict(list)
        for key, ts in shedule:
            ss[key].append(ts)
        for key, shedule in ss:
            self._tasks[key].shedule = shedule

    def check_shedule(self):
        """
            return next task to be runned
            or None if there are no tasks
        """
        return min(
            (
                self._tasks[i]
                for i in self._tasks
                if self._tasks[i].next_run
            ),
            key=lambda task: task.next_run,
        ) if self._tasks else None

    async def _chek_running_tasks(self):
        new_task_list = []
        for key, task in self._running_tasks:
            if not task.done():
                new_task_list.append((key, task))
            else:
                if task.exception() is not None:
                    await self._logger.error('Task "{}" failed with exception:\n{}', key, '\n'.join(task.get_stack()))
                else:
                    result = task.result()
                    if result:
                        await self._logger.info('Task "{}" ends with result: {}', key, result)
        self._running_tasks = new_task_list

    async def _mainloop(self):
        await self._logger.debug('planner started')
        while self.RUN:
            task = self.check_shedule()
            timeout = self.cfg.timeout
            eps = 0.1
            if task is not None:
                await self._logger.debug('next task "{}" in {:.2f} sec', task.name, task.delay)
                if abs(time.time() - task.next_run) < eps:
                    self.run_task(task.name)
                timeout = min(self.cfg.timeout, task.delay / 1.5)
            await self._chek_running_tasks()
            await asyncio.sleep(timeout)

    def run_task(self, key, run_copy=False):
        task = self._tasks[key]
        task.prepare_for_run()
        self._running_tasks.append((task.name, self.cfg.loop.create_task(task.run())))

    def add_task(self, target, **kwargs):
        key = kwargs.get('key') or ''.join(hex(i)[2:] for i in os.urandom(4)).upper()
        if key in self._tasks:
            raise ValueError(f'key "{key}" already in use')
        kwargs['key'] = key
        self._tasks[key] = Task(target=target, **kwargs)

    def run(self):
        self.task = self.cfg.loop.create_task(self._mainloop())

    def stop(self):
        self.RUN = False
