#!/usr/bin/env python3

from k2.aeon.sitemodules.base import SiteModule
from k2.aeon.responses import Response
from k2.utils.autocfg import AutoCFG
from k2.utils.http import HTTP_METHODS


class Rederict(SiteModule):
    def __init__(self, location, code=302, headers=None, methods=None):
        self._code = 302
        self._headers = AutoCFG(headers or {})
        self._headers.update(
            location=location,
        )
        for method in (methods or HTTP_METHODS):
            setattr(self, method.lower(), self._req_handler)

    async def _req_handler(self, req):
        return Response(
            code=self._code,
            headers=self._headers,
        )
