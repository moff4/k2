#!/usr/bin/env python3
import time


class AutoCFG(dict):

    def __init__(self, *a, **b):
        super().__setattr__('key_modifier', b.pop('key_modifier', None))
        super().__init__(*a, **b)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        if self.key_modifier:
            key = self.key_modifier(key)
        self[key] = value

    def __contains__(self, key):
        return super().__contains__(self.key_modifier(key) if self.key_modifier else key)

    def update(self, *args, **kwargs):
        if self.key_modifier:
            super().update(
                *[
                    {
                        self.key_modifier(k): a[k]
                        for k in a
                    }
                    for a in args
                ],
                **{
                    self.key_modifier(k): kwargs[k]
                    for k in kwargs
                },
            )


    @staticmethod
    def __deep_update(d1, d2, create=True):
        for i in d2:
            if i in d1:
                if isinstance(d2[i], dict) and isinstance(d1[i], dict):
                    d1[i] = AutoCFG.__deep_update(d1[i], d2[i], create=create)
                else:
                    d1[i] = d2[i]
            elif create:
                d1[i] = d2[i]
        return d1

    def update_fields(self, *a, **b):
        """
            only update fields
            does not create new
        """
        for d in a:
            if not isinstance(d, dict):
                raise ValueError('update_fields param must be dict')
            self.update({k: d[k] for k in d if k in self})
        self.update({k: b[k] for k in b if k in self})
        return self

    def deep_update_fields(self, *a, **b):
        for d in a:
            if not isinstance(d, dict):
                raise ValueError('deep_update_fields param must be dict')
            self.__deep_update(self, d, create=False)
        self.__deep_update(self, b, create=False)
        return self

    def update_missing(self, *a, **b):
        """
            only insert new fields
            does not update existing
        """
        for d in a:
            if not isinstance(d, dict):
                raise ValueError('update_missing param must be dict')
            self.update({k: d[k] for k in d if k not in self})
        self.update({k: b[k] for k in b if k not in self})
        return self


class CacheDict(dict):
    def __init__(self, timeout, func):
        self._timeout = timeout
        self._func = func
        super().__init__()

    def __getitem__(self, key):
        if (
            key not in self
        ) or (
            not isinstance(super().__getitem__(key), dict)
        ) or (
            super().__getitem__(key).get('time', 0) < time.time()
        ):
            super().__setitem__(
                key,
                {
                    'time': time.time() + self._timeout,
                    'data': self._func(key),
                },
            )
        return super().__getitem__(key)['data']
