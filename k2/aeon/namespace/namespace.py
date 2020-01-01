#!/usr/bin/env python3
import re
from typing import Tuple, Dict, Optional

from k2.aeon.sitemodules.base import BaseSiteModule
from k2.aeon.responses import Response
from k2.aeon.ws.handler import WSHandler
from k2.utils.autocfg import AutoCFG


class NameSpace:
    TYPE_LEAFE = 0
    TYPE_SUBTREE = 1

    def __init__(self, tree=None) -> None:
        self._keys = AutoCFG()
        if tree:
            self.create_tree(tree)

    def __contains__(self, key) -> bool:
        return key in self._keys

    def __getitem__(self, key) -> Tuple[str, str]:
        return self._keys[key]['value'], self._keys[key]['type']

    def __setitem__(self, key: str, value) -> None:
        try:
            err = (
                not isinstance(value, (BaseSiteModule, WSHandler, NameSpace, Response, dict))
            ) and (
                not issubclass(value, WSHandler)
            )
        except TypeError:
            err = True
        if err:
            raise TypeError(
                'value "{}" for key "{}" must be NameSpace, dict, BaseSiteModule, WSHandler or Response'.format(
                    value,
                    key,
                )
            )
        self._keys[key] = {
            'value': value,
            'type': (
                self.TYPE_SUBTREE
                if isinstance(value, (NameSpace, dict)) else
                self.TYPE_LEAFE
            )
        }

    def items(self):
        yield from self._keys.items()

    def find_best(self, name, args=None) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        args = args or {}
        if name in self._keys and self._keys[name]['type'] == self.TYPE_LEAFE:
            return self._keys[name]['value'], args

        if not (
             az := [
                (key, m)
                for key in self._keys
                if (m := re.match(key, name)) is not None
            ]
        ):
            return None, None

        for key, m in sorted(az, key=lambda x: x[1].end() - x[1].start(), reverse=True):
            if self._keys[key]['type'] == self.TYPE_LEAFE:
                return self._keys[key]['value'], dict(args, **m.groupdict())
            elif (
                variant := self._keys[key]['value'].find_best(
                    name=name[m.end():],
                    args=dict(args, **m.groupdict()),
                )
            )[0]:
                return variant
        return None, None

    def create_tree(self, tree) -> None:
        """
            tree - namespace or dict:
                key == name
                value - tree / BaseSiteModule / WSHandler / Response,
        """
        for key, value in tree.items():
            self[key] = (
                NameSpace(value)
                if isinstance(value, (NameSpace, dict)) else
                value
            )
