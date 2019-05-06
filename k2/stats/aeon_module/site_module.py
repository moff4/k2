#!/usr/bin/env python3

import json

from k2.aeon import Response
from k2.stats import (
    export,
    reset,
)

STATUS_OK = json.dumps({'status': 'ok'})


class StatsCGI:
    def get(self, req):
        return Response(
            data=json.dumps(
                {
                    'status': 'ok',
                    'data': export(),
                }
            ),
            code=200,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
            }
        )

    def post(self, req):
        reset(
            key=req.args.get('key', None)
        )
        return Response(code=200, data=STATUS_OK)
