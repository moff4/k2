#!/usr/bin/env python3
import re
import inspect
import logging

from k2.aeon.abstract_aeon import AbstractAeon
from k2.aeon.requests import Request
from k2.aeon.responses import Response
from k2.aeon.exceptions import AeonResponse
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

    # objects must be callable or asyncio.corutines
    middleware = []
    postware = []

    def chooser(self, req):
        for key in self.site_modules:
            m = re.match(key, req.url)
            if m is not None:
                return self.site_modules[key], m.groupdict()
        return None, None

    async def client_connected_cb(self, reader, writer):
        async def run_ware(ware, *a, **b):
            if inspect.iscoroutinefunction(ware):
                await ware(*a, **b)
            else:
                ware(*a, **b)

        keep_alive = True
        addr = writer.get_extra_info('peername')
        logging.debug('[%s:%s] new connection', *addr)
        try:
            while keep_alive:
                resp = None
                try:
                    req = Request(addr, reader, writer)
                    logging.debug('[%s:%s] gonna data read', *addr)
                    await req.read()
                    logging.debug('[%s:%s] data read', *addr)

                    module, args = self.chooser(req)
                    if module is None or not hasattr(module, req.method.lower()):
                        resp = Response(data=NOT_FOUND, code=404)
                    else:
                        for ware in self.middleware:
                            await run_ware(ware, module=module, request=req, args=args)
                        handler = getattr(module, req.method.lower())
                        if inspect.iscoroutinefunction(handler):
                            resp = await handler(req, **args)
                        else:
                            resp = handler(req, **args)
                except AeonResponse as e:
                    logging.exception('[%s:%s] ex: %s', addr[0], addr[1], e)
                    resp = Response(data=e.data, code=e.code, headers=e.headers)
                except RuntimeError as e:
                    logging.warning(e)
                    req.keep_alive = False
                except Exception as e:
                    logging.exception('[%s:%s] ex: %s', addr[0], addr[1], e)
                    req.keep_alive = False
                    resp = Response(data=SMTH_HAPPENED, code=500)

                logging.debug('[%s:%s] gonna send response', *addr)
                if resp is not None:
                    await req.send(resp)

                for ware in req.postware:
                    await run_ware(ware, module=module, request=req, args=args, response=resp)

                for ware in self.postware:
                    await run_ware(ware, module=module, request=req, args=args, response=resp)

                keep_alive = req.headers.get('connection', 'keep-alive') != 'close' and req.keep_alive
        except Exception as e:
            logging.error('[%s:%s] handler error: %s', addr[0], addr[1], e)

    def add_site_module(self, key, target):
        self.site_modules[key] = target

    def add_middleware(self, target):
        if not callable(target):
            raise TypeError('target (%s) must be callable' % target)
        self.middleware[key] = target

    def add_postware(self, target):
        if not callable(target):
            raise TypeError('target (%s) must be callable' % target)
        self.postware[key] = target
