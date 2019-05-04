#!/usr/bin/env python3

from k2.utils.http import SMTH_HAPPENED


class AeonResponse(Exception):
    def __init__(self, *a, **b):
        super().__init__(self, *a)
        self.data = b.get('data', SMTH_HAPPENED)
        self.headers = b.get('headers', None)
        self.code = b.get('code', 500)

    def __str__(self):
        return f'<AeonResponse: {self.code}>'
