#!/usr/bin/env python3


class AutoCFG(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        self[key] = value

    def update_fields(self, *a, **b):
        """
            only update fields
            does not create new
        """
        for d in a:
            self.update({k: d[k] for k in d if k in self})
        self.update({k: b[k] for k in b if k in self})
        return self
