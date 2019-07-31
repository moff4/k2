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
from k2.utils.autocfg import AutoCFG
from k2.utils.http import NOT_FOUND

STATUS_OK = dumps({'status': 'ok'})


class StatsCGI(SiteModule):
    defautls = {
        'localips': False,
        'secret-value': None,
        'secret-header': 'x-stats-secret',
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG(kwargs).update_missing(self.defautls)

    async def handle(self, request, **args):

        if (self.cfg.localips and not req.is_local()):
            return Response(code=404)

        if (
            self.cfg['secret-value']
        ) and (
            self.cfg['secret-value'] != request.headers.get(self.cfg['secret-header'], None)
        ):
            return Response(code=403)

        return await super().handle(request, **args)

    async def get(self, req):
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
