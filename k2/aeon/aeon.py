#!/usr/bin/env python3
import re
import asyncio
import logging

from k2.aeon.abstract_aeon import AbstractAeon
from k2.aeon.requests import Request
from k2.aeon.responses import Response
from k2.aeon.exceptions import AeonResponse
from k2.aeon.ws import WSHandler
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    NOT_FOUND,
    HTTP_METHODS,
    SMTH_HAPPENED,
)


class Aeon(AbstractAeon):
    """
        asyncio web server
    """

    # key - url as regular expression
    # value - dict:
    #  target -> site_module / WSHandler
    #  type -> 'cgi' / 'ws'
    _endpoints = {}

    # objects must be callable or asyncio.corutines
    middleware = []
    postware = []

    def chooser(self, req):
        """
            find enpoint
            return (endpoint dict, params)
            or (None, None)
        """
        for key in self._endpoints:
            m = re.match(key, req.url)
            if m is not None:
                return self._endpoints[key], m.groupdict()
        return None, None

    async def client_connected_cb(self, reader, writer):
        async def run_ware(ware, *a, **b):
            if asyncio.iscoroutinefunction(ware):
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

                    endpoint, args = self.chooser(req)
                    if endpoint.type == 'cgi':
                        module = endpoint.target
                        if (
                            module is None
                        ) or (
                            req.method not in enpoint.methods
                        ) or (
                            not hasattr(module, req.method.lower())
                        ):
                            resp = Response(data=NOT_FOUND, code=404)
                        else:
                            for ware in self.middleware:
                                await run_ware(ware, module=module, request=req, args=args)
                            handler = getattr(module, req.method.lower())
                            if asyncio.iscoroutinefunction(handler):
                                resp = await handler(req, **args)
                            else:
                                resp = handler(req, **args)
                    elif endpoint.type == 'ws':
                        if req.headers.get('upgrade', '').lower() == 'websocket':
                            await endpoint.target(req, **args).mainloop()
                            keep_alive = False
                        else:
                            resp = Response(data=NOT_FOUND, code=404)
                    else:
                        resp = Response(data=NOT_FOUND, code=404)
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
            logging.error(f'[{addr[0]}:{addr[1]}] handler error: {e}')

    def add_site_module(self, key, target, methods=None):
        if methods is None:
            cgi_methods = HTTP_METHODS
        else:
            cgi_methods = set()
            for i in methods:
                i = i.upper()
                if i in HTTP_METHODS:
                    cgi_methods.add(i)
                else:
                    raise ValueError(f'Unallowed HTTP-method "{i}"')

        self._endpoints[key] = AutoCFG(
            {
                'target': target,
                'type': 'cgi',
                'methods': cgi_methods,
            }
        )

    def add_middleware(self, target):
        if not callable(target):
            raise TypeError(f'target ({target}) must be callable')
        self.middleware.append(target)

    def add_postware(self, target):
        if not callable(target):
            raise TypeError(f'target ({target}) must be callable')
        self.postware.append(target)

    def add_ws_handler(self, key, target):
        if not issubclass(target, WSHandler):
            raise TypeError(f'target ({target}) must be subclass of WSHandler')
        self._endpoints[key] = AutoCFG(
            {
                'target': target,
                'type': 'ws'
            }
        )
