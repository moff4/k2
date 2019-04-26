#!/usr/bin/env python3
import re

from k2.aeon.abstract_aeon import AbstractAeon
from k2.aeon.requests import Request
from k2.aeon.responses import Response
from k2.utils.http import (
    NOT_FOUND,
    SMTH_HAPPENED,
)


class Aeon(AbstractAeon):
    """
        asyncio web server
    """

    # key - url as regular expression
    # value - callable site_module
    site_modules = {}

    # objects must be asyncio.corutines
    middleware = []
    postware = []

    def chooser(self, req):
        for key in self.site_modules:
            m = re.match(key, req.url)
            if m is not None:
                return self.site_modules[key], m.groupdict()
        return None, None

    async def client_connected_cb(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.log.debug('[%s:%s] new connection', *addr)
        try:
            # while connection keep-alive:
            req = Request(addr, reader, writer)
            await req.read()
            self.log.debug('[%s:%s] data read', *addr)

            module, args = self.chooser(req)
            if module is None:
                resp = Response(data=NOT_FOUND, code=404)
            else:
                for ware in self.middleware:
                    await ware(module=module, request=req, args=args)
                resp = module(request=req, **args)

            self.log.debug('[%s:%s] gonna send response', *addr)
            await req.send(resp)

            for ware in req.postware:
                await ware(module=module, request=req, args=args, response=resp)

            for ware in self.postware:
                await ware(module=module, request=req, args=args, response=resp)
        except Exception as e:
            self.log.error('[%s:%s] handler error: %s', addr[0], addr[1], e)
            await req.send(Response(data=SMTH_HAPPENED, code=500))

    # add site_module
    # add middleware
    # add postware
