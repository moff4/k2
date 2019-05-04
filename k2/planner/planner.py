#!/usr/bin/env python3
import asyncio
import time

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

    async def _mainloop(self):
        while self.RUN:
            task = self.check_shedule()
            timeout = self.cfg.timeout
            eps = 0.1
            if task is not None:
                if abs(time.time() - task.next_run) < eps:
                    self._running_tasks.append(
                        self.cfg.loop.create_task(
                            task.run(),
                            # self.cfg.loop,
                        )
                    )
                timeout = min(self.cfg.timeout, task.delay / 1.5)
            print(timeout, task.next_run, task.delay)
            await asyncio.sleep(timeout)

    def add_task(self, key, target, **kwargs):
        if key in self._tasks:
            raise ValueError('key "{}" already in use'.format(key))
        self._tasks[key] = Task(target=target, **kwargs)

    def run(self):
        self.task = self.cfg.loop.create_task(
            self._mainloop()
        )

    def stop(self):
        self.RUN = False