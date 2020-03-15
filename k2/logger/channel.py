#!/usr/bin/env python3
import re
import sys
import time
import asyncio
import logging
import traceback
from typing import Dict, Tuple, Any, Union, List, Optional, Iterable
from multiprocessing import (
    Lock,
    synchronize,
)

from k2.utils.autocfg import AutoCFG

Locks = {}  # type: Dict[str, synchronize.Lock]

CHANNEL_DEFAULTS = {
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


class Channel:

    def __init__(self, **kwargs) -> None:
        self.cfg = AutoCFG(CHANNEL_DEFAULTS).update_fields(kwargs)
        if self.cfg.key is not None:
            if any((re.match(f'--stdout=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.stdout = True
            if any((re.match(f'--debug=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.log_levels.add('debug')
            if any((re.match(f'--no-log=.*{self.cfg.key}.*', x) is not None for x in sys.argv)):
                self.cfg.autosave = False

        if self.cfg.autosave and self.cfg.log_file not in Locks:
            Locks[self.cfg.log_file] = Lock()
        self.parents = []  # type: List[Dict[str, Union[Channel, Iterable]]]
        self._logs = []  # type: List[Dict[str, Union[str, int]]]
        self._t = 0
        self._logger = logging.Logger(self.cfg.key)

    def _clear(self) -> None:
        if self._t != (_t := int(time.time())):
            self._t = _t
            _t -= self.cfg.timeout
            while self._logs and self._logs[0]['timestamp'] > _t:
                self._logs.pop(0)

    def update(self, **kwargs) -> None:
        self.cfg.update_fields(kwargs)

    def add_parent(self, parent, inherite_rights: Optional[Iterable] = None) -> None:
        if inherite_rights is None:
            inherite_rights = {'stdout', 'log_levels', 'autosave'}
        self.parents.append(
            {
                'parent': parent,
                'inherite_rights': inherite_rights,
            }
        )
        for i in {'stdout', 'autosave'}:
            self.cfg[i] |= parent.cfg[i]
        if 'log_levels' in inherite_rights:
            self.cfg.log_levels.update(parent.cfg.log_levels)

    async def log(
        self,
        msg: str,
        level: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        from_child: bool = False,
    ) -> None:
        if level not in self.cfg.log_levels:
            return
        args = args or tuple()
        kwargs = kwargs or {}
        log_msg = self.cfg.log_format.format(
            timestamp=time.strftime(self.cfg.time_format, time.localtime(timestamp := time.time())),
            level=level,
            key=self.cfg.key,
            msg=msg,
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
                with Locks[self.cfg.log_file]:
                    with open(self.cfg.log_file, 'a') as f:
                        f.write(''.join([log_msg, '\n']))
        if self.cfg.callback is not None:
            params = {
                'key': self.cfg.key,
                'level': level,
                'raw_msg': msg,
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

    @staticmethod
    def __form_msg_(msg: str, *a, **b):
        if isinstance(msg, str):
            return msg.format(*a, **b)
        else:
            return ', '.join(
                [
                    str(i)
                    for i in [msg] + list(a) + list(b.items())
                ]
            )

    async def exception(self, msg: str, *args, **kwargs):
        await self.log(
            msg=''.join([self.__form_msg_(msg, *args, **kwargs), '\n', *traceback.format_exception(*sys.exc_info())]),
            level=kwargs.get('level', 'error'),
            args=args,
            kwargs=kwargs,
        )

    async def error(self, msg: str, *args, **kwargs):
        await self.log(
            msg=self.__form_msg_(msg, *args, **kwargs),
            level='error',
            args=args,
            kwargs=kwargs,
        )

    async def warning(self, msg: str, *args, **kwargs):
        await self.log(
            msg=self.__form_msg_(msg, *args, **kwargs),
            level='warning',
            args=args,
            kwargs=kwargs,
        )

    async def info(self, msg: str, *args, **kwargs):
        await self.log(
            msg=self.__form_msg_(msg, *args, **kwargs),
            level='info',
            args=args,
            kwargs=kwargs,
        )

    async def debug(self, msg: str, *args, **kwargs):
        await self.log(
            msg=self.__form_msg_(msg, *args, **kwargs),
            level='debug',
            args=args,
            kwargs=kwargs,
        )

    def clear(self):
        self._logs.clear()

    def export(self) -> List[Dict[str, Union[str, int]]]:
        return self._logs
