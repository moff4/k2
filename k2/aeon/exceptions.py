#!/usr/bin/env python3

from k2.aeon.responses import Response


class AeonResponse(Exception):
    def __init__(self, *a, **b):
        super().__init__(self, *a)
        self._msg = a[0] if a else '-'
        self.data = b.get('data', '')
        self.headers = b.get('headers', None)
        self.code = b.get('code', 500)
        self.cookies = b.get('cookies', {})
        self.close_conn = b.get('close_conn', False)
        self.silent = b.get('silent', False)
        self._resp = None

    def __str__(self):
        return '<AeonResponse [{code}] {msg}>'.format(
            msg=self._msg,
            code=self.code,
        )

    @property
    def response(self):
        if self._resp:
            return self._resp
        if self.silent:
            return
        self._resp = Response(
            data=self.data,
            code=self.code,
            headers=self.headers,
            cookies=self.cookies,
        )
        if self.close_conn:
            self._resp.headers['connection'] = 'close'
        return self._resp
