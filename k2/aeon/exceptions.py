#!/usr/bin/env python3


class AeonResponse(Exception):
    def __init__(self, *a, **b):
        super().__init__(self, *a)
        self.data = b.get('data', '')
        self.headers = b.get('headers', None)
        self.code = b.get('code', 500)
        self.cookies = b.get('cookies', {})

    def __str__(self):
        return f'<AeonResponse: {self.code}>'
