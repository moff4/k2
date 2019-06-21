#!/usr/bin/env python3
import re

from k2.aeon.sitemodules.base import SiteModule
from k2.aeon.ws.handler import WSHandler
from k2.utils.autocfg import AutoCFG


class NameSpace:
    TYPE_LEAFE = 0
    TYPE_SUBTREE = 1

    def __init__(self, tree=None):
        self._keys = AutoCFG()
        if tree:
            self.create_tree(tree)

    def __contains__(self, key):
        return key in self._keys

    def __getitem__(self, key):
        return (self._keys[key]['value'], self._keys[key]['type'])

    def __setitem__(self, key, value):
        try:
            err = (
                not isinstance(value, (SiteModule, WSHandler, NameSpace, dict))
            ) and (
                not issubclass(value, (SiteModule, WSHandler))
            )
        except TypeError:
            err = True
        if err:
            raise TypeError(
                'value "{}" for key "{}" must be NameSpace, dict, SiteModule or WSHandler'.format(
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

    def find_best(self, name, args=None):
        args = args or {}
        if name in self._keys and self._keys[name]['type'] == self.TYPE_LEAFE:
            return self._keys[name]['value'], args

        az = []
        for key in self._keys:
            m = re.match(key, name)
            if m is not None:
                az.append((key, m))

        if not az:
            return None, None

        for key, _args in sorted(az, key=lambda x: x[1].end() - x[1].start(), reverse=True):
            if self._keys[key]['type'] == self.TYPE_LEAFE:
                return self._keys[key]['value'], args
            else:
                target, _args = self._keys[key]['value'].find_best(
                    name=name[m.end():],
                    args=dict(args, **m.groupdict()),
                )
                if target:
                    return target, _args
        return None, None

    def create_tree(self, tree):
        """
            tree - namespace or dict:
                key == name
                value - tree / SiteModule / WSHandler,
        """
        for key, value in tree.items():
            self[key] = (
                NameSpace(value)
                if isinstance(value, (NameSpace, dict)) else
                value
            )
