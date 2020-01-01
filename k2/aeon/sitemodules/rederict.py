#!/usr/bin/env python3

from k2.aeon.sitemodules.base import BaseSiteModule
from k2.aeon.responses import Response
from k2.utils.autocfg import AutoCFG
from k2.utils.http import HTTP_METHODS


class Rederict(BaseSiteModule):
    def __init__(self, location=None, code=302, headers=None, methods=None, url_modifier=None):
        if not location and not url_modifier:
            raise ValueError('must be passed "location" or "url_modifier"')
        self._code = 302
        self._headers = AutoCFG(headers or {})
        self._url_modifier = url_modifier
        if not url_modifier:
            self._headers.update(location=location)
        for method in (methods or HTTP_METHODS):
            setattr(self, method.lower(), self._req_handler)

    async def _req_handler(self, req):
        headers = dict(self._headers)
        if self._url_modifier:
            headers.update(location=self._url_modifier(req))
        return Response(
            code=self._code,
            headers=headers,
        )
