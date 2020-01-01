#!/usr/bin/env python3

import gzip

try:
    import ujson as json
except ImportError:
    import json

from k2.aeon.responses.base_response import Response


class ClientResponse(Response):

    def __init__(self, **b):
        try:
            if 'headers' in b and b.get('data') and b['headers'].get('content-encoding') == 'gzip':
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
        return json.loads(self._data) if self._data else {}
