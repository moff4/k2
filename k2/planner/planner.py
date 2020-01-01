#!/usr/bin/env python3
import os
import asyncio
import time
from collections import defaultdict
from typing import List, Tuple

import k2.logger as logger
from k2.planner.task import Task
from k2.utils.autocfg import AutoCFG

PLANNER_DEFAULTS = {
    'timeout': 5.0,
    'loop': None
}


class Planner:
    """
        cron service
    """

    def __init__(self, **kwargs) -> None:
        self.cfg = AutoCFG(PLANNER_DEFAULTS).update_fields(kwargs)
        self.RUN = True
        self.task = None
        self.cfg.loop = self.cfg.loop or asyncio.get_event_loop()
        self._tasks = {}
        self._running_tasks = []
        self._logger = logger.new_channel(
            key='planner',
            parent=logger.get_channel('base_logger'),
        )

    @property
    def shedule(self) -> List[Tuple[str, float]]:
        """
            return shedule for all tasks
            as list of tuples(task-name, timestamp)
        """
        return sorted(
            [
                (key, ts)
                for key, task in self._tasks.items()
                for ts in task.shedule
            ],
            key=lambda x: x[1],
        )

    @shedule.setter
    def shedule(self, shd) -> None:
        """
            takes list of tuples as shedule for all tasks
            and upd each task shedules
        """
        ss = defaultdict(list)
        for key, ts in shd:
            ss[key].append(ts)
        for key, shd in ss:
            self._tasks[key].shedule = shd

    def check_shedule(self) -> List[Task]:
        """
            return list of task to be runned
            or empty list if there are no tasks to run NOW
        """
        return sorted(
            (
                task
                for key in self._tasks
                if (task := self._tasks[key]).next_run
            ),
            key=lambda task: task.next_run,
        ) if self._tasks else []

    async def _check_running_tasks(self) -> None:
        new_task_list = []
        for key, task in self._running_tasks:
            if not task.done():
                new_task_list.append((key, task))
            elif task.exception():
                await self._logger.error('Task "{}" failed with exception:\n{}', key, '\n'.join(task.get_stack()))
            elif result := task.result():
                await self._logger.info('Task "{}" ends with result: {}', key, result)
        self._running_tasks = new_task_list

    async def _mainloop(self) -> None:
        await self._logger.debug('planner started')
        eps = 0.1
        while self.RUN:
            tasks = self.check_shedule()
            timeout = self.cfg.timeout
            for task in tasks:
                await self._logger.debug('next task "{}" in {:.2f} sec', task.name, task.delay)
                self.run_task(task.name)
                timeout = min([self.cfg.timeout, task.delay / 1.5, timeout])
            await self._check_running_tasks()
            await asyncio.sleep(timeout)

    def run_task(self, key: str) -> None:
        task = self._tasks[key]
        task.prepare_for_run()
        self._running_tasks.append((task.name, self.cfg.loop.create_task(task.run())))

    def add_task(self, target, **kwargs) -> None:
        if (key := kwargs.get('key') or ''.join(hex(i)[2:] for i in os.urandom(4)).upper()) in self._tasks:
            raise ValueError(f'key "{key}" already in use')
        kwargs['key'] = key
        self._tasks[key] = Task(target=target, **kwargs)

    def run(self) -> None:
        self.task = self.cfg.loop.create_task(self._mainloop())

    def stop(self) -> None:
        self.RUN = False
        try:
            self.task.cancel()
        except Exception:
            ...
