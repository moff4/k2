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
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG(kwargs).update_missing(self.defautls)

    async def get(self, req):
        if not self.cfg.localips or (self.cfg.localips and req.is_local()):
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
        else:
            return Response(code=404, data=NOT_FOUND)

    async def post(self, req):
        if not self.cfg.localips or (self.cfg.localips and req.is_local()):
            await reset(
                key=req.args.get('key', None)
            )
            return Response(code=200, data=STATUS_OK)
        else:
            return Response(code=404, data=NOT_FOUND)
