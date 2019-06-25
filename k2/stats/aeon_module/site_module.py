#!/usr/bin/env python3

try:
    from ujson import dumps
except ImportError:
    from json import dumps

from k2.aeon import (
    Response,
    SiteModule,
)
from k2.stats import (
    export,
    reset,
)

STATUS_OK = dumps({'status': 'ok'})


class StatsCGI(SiteModule):
    def get(self, req):
        return Response(
            data=dumps(
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

    async def post(self, req):
        await reset(
            key=req.args.get('key', None)
        )
        return Response(code=200, data=STATUS_OK)
