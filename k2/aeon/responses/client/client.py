#!/usr/bin/env python3

import gzip

try:
    from ujson import loads
except ImportError:
    from json import loads

from k2.aeon.responses.base_response import Response


class ClientResponse(Response):

    def __init__(self, **b):
        try:
            if 'headers' in b and b.get('data'):
                if b['headers'].get('content-encoding') == 'gzip':
                    b['data'] = gzip.decompress(b['data'])
        finally:
            super().__init__(**b)

    @property
    def ok(self):
        return 200 <= self.code < 300

    @property
    def text(self):
        if isinstance(self._data, str):
            return self._data
        try:
            return self._data.decode()
        except Exception:
            return self._data

    def json(self):
        if self._data:
            return loads(self._data)
        else:
            return {}
