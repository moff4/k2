#!/usr/bin/env python3
import re
import asyncio

from k2.aeon.abstract_aeon import AbstractAeon
from k2.aeon.requests import Request
from k2.aeon.responses import Response
from k2.aeon.exceptions import AeonResponse
from k2.aeon.sitemodules.base import SiteModule
from k2.aeon.ws import WSHandler
from k2.aeon.namespace import NameSpace
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    NOT_FOUND,
    HTTP_METHODS,
    SMTH_HAPPENED,
)
import k2.stats.stats as stats


class Aeon(AbstractAeon):
    """
        asyncio web server
    """

    # objects must be callable or asyncio.corutines
    middleware = []
    postware = []

    def __init__(self, *a, **b):
        super().__init__(**b)
        self._request_prop = b.get('request', {})
        self.namespace = NameSpace(
            tree=b.get('namespace'),
        )
        for i in range(1, 6):
            stats.new(key=f'aeon-{i}xx', type='time_event_counter', description=f'HTTP status code {i}xx')
        stats.new(key='request_log', type='time_events', description='log for each request')
        stats.new(key='ws_connections', type='counter', description='opened ws conenctions')
        stats.new(key='connections', type='counter', description='opened conenctions')

    async def client_connected_cb(self, reader, writer):
        async def run_ware(ware, *a, **b):
            if asyncio.iscoroutinefunction(ware):
                await ware(*a, **b)
            else:
                ware(*a, **b)

        _log_extras = '' if writer.get_extra_info('socket').getsockname()[1] != self.cfg.https_port else '[ssl] '

        keep_alive = True
        addr = writer.get_extra_info('peername')
        await self._logger.debug(_log_extras + f'new connection from {addr[0]}:{addr[1]}')
        await stats.add('connections')
        try:
            while keep_alive:
                try:
                    _ssl = writer.get_extra_info('socket').getsockname()[1] == self.cfg.https_port
                except Exception as e:
                    await self._logger.error('get_extra_info(\'socket\'): {}', e)
                    _ssl = False
                resp = None
                req = Request(
                    addr=addr,
                    reader=reader,
                    writer=writer,
                    ssl=_ssl,
                    **self._request_prop,
                )
                try:
                    await req.logger.debug(f'gonna read data')
                    await req.read()
                    await req.logger.debug(f'data read')

                    await stats.add(key='request_log', value=f'{req.method} {req.url} {req.args}')

                    module, args = self.namespace.find_best(req.url)
                    if not module:
                        resp = Response(data=NOT_FOUND, code=404)

                    elif isinstance(module, WSHandler):
                        if req.headers.get('upgrade', '').lower() == 'websocket':
                            await req.upgrade_to_ws(module, **args)
                            req.keep_alive = False
                            resp = None
                        else:
                            resp = Response(data=NOT_FOUND, code=404)

                    elif isinstance(module, SiteModule) or issubclass(module, SiteModule):
                        if not hasattr(module, req.method.lower()):
                            resp = Response(data=NOT_FOUND, code=404)
                        else:
                            for ware in self.middleware:
                                await run_ware(ware, module=module, request=req, args=args)
                            handler = getattr(module, req.method.lower())
                            if asyncio.iscoroutinefunction(handler):
                                resp = await handler(req, **args)
                            else:
                                resp = handler(req, **args)
                    else:
                        resp = Response(data=NOT_FOUND, code=404)
                except AeonResponse as e:
                    resp = Response(data=e.data, code=e.code, headers=e.headers, cookies=e.cookies)
                except (RuntimeError, ConnectionResetError):
                    req.keep_alive = False
                except Exception as e:
                    await req.logger.exception('aeon-loop ex: {}', e)
                    req.keep_alive = False
                    resp = Response(data=SMTH_HAPPENED, code=500)

                if resp is not None:
                    await req.logger.debug('gonna send response')
                    await req.send(resp)

                for ware in req.postware:
                    await run_ware(ware, module=module, request=req, args=args, response=resp)

                for ware in self.postware:
                    await run_ware(ware, module=module, request=req, args=args, response=resp)

                keep_alive = req.headers.get('connection', 'keep-alive') != 'close' and req.keep_alive
        except Exception as e:
            await self._logger.exception('handler error: {}', e)
        finally:
            await stats.add('connections', -1)

    def add_namespace(self, namespace):
        self.namespace.create_tree(namespace)

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

        self.namespace[key] = target

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
        self.namespace[key] = target
