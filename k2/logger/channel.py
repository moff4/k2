#!/usr/bin/env python3
import re
import sys
import time
import asyncio
import traceback

from k2.utils.autocfg import AutoCFG


class Channel:
    defaults = {
        'key': None,
        'timeout': 3600,
        'limit': 1000,
        'autosave': '--no-log' not in sys.argv,
        'log_file': 'log.txt',
        'callback': None,
        'stdout': '--stdout' in sys.argv,
        'time_format': '%d.%m.%Y %H:%M:%S',
        'log_levels': {'info', 'warning', 'error'}.union({'debug'} if '--debug' in sys.argv else set()),
        'log_format': '{timestamp} -:- {level} [{key}] {msg}',
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG(self.defaults).update_fields(kwargs)
        if self.cfg.key is not None:
            if any((re.match(f'--stdout=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.stdout = True
            if any((re.match(f'--debug=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.log_levels.add('debug')
            if any((re.match(f'--no-log=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.autosave = False

        self.parents = []
        self._logs = []
        self._t = 0

    def _clear(self):
        _t = int(time.time())
        if self._t != self._t:
            self._t = _t
            _t -= self.cfg.timeout
            while self._logs and self._logs[0]['timestamp'] > _t:
                self._logs.pop(0)

    def update(self, **kwargs):
        self.cfg.update_fields(kwargs)

    def add_parent(self, parent, inherite_rights={'stdout', 'log_levels', 'autosave'}):
        self.parents.append(
            {
                'parent': parent,
                'inherite_rights': inherite_rights,
            }
        )
        for i in {'stdout', 'autosave'}:
            self.cfg[i] |= parent.cfg[i]
        if 'log_levels' in inherite_rights:
            self.cfg.log_levels.update(self.parent.cfg.log_levels)

    async def log(self, msg, level, args, kwargs, from_child=False):
        if level not in self.cfg.log_levels:
            return

        timestamp = time.time()
        raw_msg = msg.format(*args, **kwargs)
        log_msg = self.cfg.log_format.format(
            timestamp=time.strftime(self.cfg.time_format, time.localtime(timestamp)),
            level=level,
            key=self.cfg.key,
            msg=raw_msg,
        )

        self._logs.append(
            {
                'timestamp': timestamp,
                'log_msg': log_msg,
            }
        )
        if not from_child:
            if self.cfg.stdout:
                print(log_msg)
            if self.cfg.autosave:
                with open(self.cfg.log_file, 'a') as f:
                    f.write(''.join([log_msg, '\n']))
        if self.cfg.callback is not None:
            params = {
                'key': self.cfg.key,
                'level': level,
                'raw_msg': raw_msg,
                'log_msg': log_msg,
            }

            if asyncio.iscoroutinefunction(self.cfg.callback):
                await self.cfg.callback(**params)
            elif callable(self.cfg.callback):
                self.cfg.callback(**params)

        await asyncio.gather(
            *[
                parent['parent'].log(
                    msg=msg,
                    level=level,
                    args=args,
                    kwargs=kwargs,
                    from_child=True,
                )
                for parent in self.parents
            ]
        )

    async def exception(self, msg, level='error', *args, **kwargs):
        await self.log(
            msg=''.join([msg, '\n'] + traceback.format_exception(*sys.exc_info())),
            level=level,
            args=args,
            kwargs=kwargs,
        )

    async def error(self, msg, *args, **kwargs):
        await self.log(
            msg=msg,
            level='error',
            args=args,
            kwargs=kwargs,
        )

    async def warning(self, msg, *args, **kwargs):
        await self.log(
            msg=msg,
            level='warning',
            args=args,
            kwargs=kwargs,
        )

    async def info(self, msg, *args, **kwargs):
        await self.log(
            msg=msg,
            level='info',
            args=args,
            kwargs=kwargs,
        )

    async def debug(self, msg, *args, **kwargs):
        await self.log(
            msg=msg,
            level='debug',
            args=args,
            kwargs=kwargs,
        )

    def clear(self):
        self._logs = []

    def export(self):
        return self._logs
