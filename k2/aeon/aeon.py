#!/usr/bin/env python3

from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Type,
)

from k2.aeon.abstract_aeon import AbstractAeon
from k2.aeon.requests import Request
from k2.aeon.responses import Response
from k2.aeon.exceptions import AeonResponse
from k2.aeon.sitemodules.base import BaseSiteModule
from k2.aeon.ws import WSHandler
from k2.aeon.namespace import NameSpace
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    NOT_FOUND,
    SMTH_HAPPENED,
    run_ware,
)
import k2.stats.stats as stats


class Aeon(AbstractAeon):
    """
        asyncio web server
    """

    # objects must be callable or asyncio.corutines
    middleware = []  # type: List[Callable]
    postware = []  # type: List[Callable]

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

    async def _handle_request(self, request: Request, _run_ware: bool = True):
        try:
            module, args = self.namespace.find_best(request.url)
            if not module:
                resp = Response(data=NOT_FOUND, code=404)

            elif isinstance(module, WSHandler):
                await request.logger.debug('found ws-handler: {}', module)
                if request.headers.get('upgrade', '').lower() == 'websocket':
                    await request.upgrade_to_ws(module, **args)
                    request.keep_alive = False
                    resp = None
                else:
                    resp = Response(data=NOT_FOUND, code=404)

            elif isinstance(module, BaseSiteModule):
                await request.logger.debug('found module: {}', module)
                if _run_ware:
                    for ware in self.middleware:
                        await run_ware(ware, module=module, request=request, args=args)
                resp = await module.handle(request=request, **args)

            elif isinstance(module, Response):
                resp = module
            else:
                resp = Response(data=NOT_FOUND, code=404)

        except AeonResponse as e:
            resp = e.response

        except (RuntimeError, ConnectionResetError):
            request.keep_alive = False
            resp = None

        except Exception as e:
            await request.logger.exception('aeon-loop ex: {}', e)
            request.keep_alive = False
            resp = Response(data=SMTH_HAPPENED, code=500)

        if resp and _run_ware:
            for ware in request.postware:
                await run_ware(ware, module=module, request=request, args=args, response=resp)
            for ware in self.postware:
                await run_ware(ware, module=module, request=request, args=args, response=resp)

        return resp

    async def client_connected_cb(self, reader, writer):
        _log_extras = '' if writer.get_extra_info('socket').getsockname()[1] != self.cfg.https_port else '[ssl] '

        resp = None
        keep_alive = True
        addr = writer.get_extra_info('peername')
        await self._logger.debug(_log_extras + f'new connection from {addr[0]}:{addr[1]}')
        await stats.add('connections', 1)
        try:
            while keep_alive:
                try:
                    _ssl = writer.get_extra_info('socket').getsockname()[1] == self.cfg.https_port
                except Exception as e:
                    await self._logger.error('get_extra_info(\'socket\'): {}', e)
                    _ssl = False
                request = Request(
                    addr=addr,
                    reader=reader,
                    writer=writer,
                    ssl=_ssl,
                    **self._request_prop,
                )
                try:
                    await request.read()
                except RuntimeError:
                    request.keep_alive = False
                except AeonResponse as e:
                    resp = e.response
                else:
                    await stats.add(key='request_log', value=f'{request.method} {request.url} {request.args}')
                    resp = await self._handle_request(request)

                if resp is not None:
                    await request.logger.debug('gonna send response')
                    await request.send(resp)

                keep_alive = 'close' not in {
                    request.headers.get('connection', 'keep-alive'),
                    resp.headers.get('connection', 'keep-alive') if resp else 'close',
                } and request.keep_alive and not reader.at_eof() and not writer.is_closing()
        except Exception as e:
            await self._logger.exception('handler error: {}', e)
        finally:
            await stats.add('connections', -1)
            try:
                await writer.drain()
                writer.close()
            except ConnectionError:
                pass

    async def emulate_request(
        self,
        url: str,
        headers: Dict[str, str] = None,
        args: Dict[str, str] = None,
        data: Optional[bytes] = None,
        method: str = 'GET',
        http_version: str = 'HTTP/1.1',
        _run_ware: bool = False,
    ) -> Response:
        """
            imulate incoming request
            usefull for testing
        """
        request = Request(
            addr=('127.0.0.1', 0),
            reader=None,
            writer=None,
            **self._request_prop,
        )
        request.init_from_dict(
            AutoCFG(
                {
                    'url': url,
                    'headers': headers or {},
                    'args': args or {},
                    'method': method,
                    'http_version': http_version,
                    'data': data or b'',
                }
            )
        )
        return await self._handle_request(request, _run_ware=_run_ware)

    def add_namespace(self, namespace: NameSpace) -> None:
        self.namespace.create_tree(namespace)

    def add_site_module(self, key, target: BaseSiteModule) -> None:
        self.namespace[key] = target

    def add_middleware(self, target: List[Callable]) -> None:
        if not callable(target) and not asyncio.iscoroutinefunction(target):
            raise TypeError(f'target ({target}) must be callable or awatable')
        self.middleware.append(target)

    def add_postware(self, target: List[Callable]) -> None:
        if not callable(target) and not asyncio.iscoroutinefunction(target):
            raise TypeError(f'target ({target}) must be callable or awatable')
        self.postware.append(target)

    def add_ws_handler(self, key, target: Type[WSHandler]) -> None:
        if not issubclass(target, WSHandler):
            raise TypeError(f'target ({target}) must be subclass of WSHandler')
        self.namespace[key] = target
