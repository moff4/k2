#!/usr/bin/env python3


class AeonResponse(Exception):
    def __init__(self, *a, **b):
        super().__init__(self, *a)
        self.data = b.get('data', '')
        self.headers = b.get('headers', None)
        self.code = b.get('code', 500)
        self.cookies = b.get('cookies', {})
        self.close_conn = b.get('close_conn', False)
        self.silent = b.get('silent', False)

    def __str__(self):
        return f'<AeonResponse: {self.code}>'
