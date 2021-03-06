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
from k2.utils.http import NOT_FOUND, FORBIDDEN

STATUS_OK = dumps({'status': 'ok'})

STATS_CGI_DEFAULTS = {
    'localips': False,
    'secret-value': None,
    'secret-header': 'x-stats-secret',
}


class StatsCGI(SiteModule):
    def __init__(self, **kwargs):
        self.cfg = AutoCFG(kwargs).update_missing(STATS_CGI_DEFAULTS)

    async def handle(self, request, **args):
        if self.cfg.localips and not request.is_local():
            return Response(code=404, data=NOT_FOUND)

        if self.cfg['secret-value'] != request.headers.get(self.cfg['secret-header'], None):
            return Response(code=403, data=FORBIDDEN)

        return await super().handle(request, **args)

    @staticmethod
    def get():
        return Response(
            data=dumps(
                {
                    'status': 'ok',
                    'data': export(),
                }
            ),
            code=200,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )

    async def post(self, req):
        await reset(key=req.args.get('key', None))
        return Response(code=200, data=STATUS_OK)
