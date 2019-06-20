#!/usr/bin/env python3
import re
from k2.utils.autocfg import AutoCFG


class NameSpace:
    TYPE_SITEMODULE = 'sitemodule'
    TYPE_NAMESPACE = 'namespace'

    def __init__(self, tree=None):
        self._keys = AutoCFG()
        if tree:
            self.create_tree(tree)

    def __contains__(self, key):
        return key in self._keys

    def __getitem__(self, key):
        return (self._keys[key]['value'], self._keys[key]['type'])

    def __setitem__(self, key, value):
        self._keys[key] = {
            'value': value,
            'type': (
                self.TYPE_NAMESPACE
                if isinstance(value, NameSpace) else
                self.TYPE_SITEMODULE
            )
        }

    def find_best(self, name, args=None):
        args = args or {}
        if name in self._keys and self._keys[name]['type'] == self.TYPE_SITEMODULE:
            return self._keys[name]['value'], args

        az = []
        for key in self._keys:
            m = re.match(key, name)
            if m is not None:
                az.append((key, m.groupdict()))

        if not az:
            return None, None

        for key, _args in sorted(az, key=lambda x: len(x[0])):
            if self._keys[key]['type'] == self.TYPE_SITEMODULE:
                return self._keys[key]['value'], args
            else:
                target, _args = self._keys[key]['value'].find_best(name, dict(args, **_args))
                if target:
                    return target, _args
        return None, None

    def create_tree(self, tree):
        """
            tree - dict:
                key == name
                value - tree(dict) or SiteModule,
        """
        for key, value in tree.items():
            self[key] = (
                NameSpace(value)
                if isinstance(value, dict) else
                value
            )
