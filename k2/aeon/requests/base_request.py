#!/usr/bin/env python3

import k2.logger as logger
from k2.aeon.parser import parse_data
from k2.aeon.ws import WSHandler
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    is_local_ip
)
import k2.stats.stats as stats


class Request:
    """
        class for each request
        must be args:
            addr - tuple (ip,port)
            reader - io stream
            writer - io stream
        kwargs:
            request_header - str: Request-ID HTTP-header (lower case) (default: x-request-id)
            believe_x_from_y - bool: if True source ip = X-From-Y (default: False)
            cache_min - int - seconds for HTTP header 'Cache-Control: max-age'
            max_header_length - max length of any HTTP-header (default: 1024B)
            max_header_count - max amount of HTTP-headers (default: 64)
            max_data_length - max length of data (default: 8MB)
            allowed_methods -  set/list of allowed HTTP methods (default: {'GET', 'POST', 'HEAD', 'PUT', 'DELETE'})
            allowed_http_version - set/list of allowed HTTP version (default: {'HTTP/1.1'})
    """

    defaults = {
        'request_header': 'x-request-id',
        'believe_x_from_y': False,
        'cache_min': 120,
    }

    # objects must be asyncio.corutines
    postware = []

    def __init__(self, addr, reader, writer, **kwargs):
        self._initialized = False
        self.cfg = AutoCFG(self.defaults).update_fields(kwargs)
        self.logger = logger.new_channel(f'{addr[0]}:{addr[1]}', parent='aeon')
        self._kwargs = kwargs
        self._addr = addr
        self._reader = reader
        self._writer = writer
        self._source_ip = self._addr[0]
        self.port = self._addr[1]
        self.keep_alive = True

        self._real_ip = self._addr
        self._url = None
        self._args = {}
        self._method = None
        self._http_version = None
        self._headers = {}
        self._data = b''
        self._ssl = kwargs.get('ssl', False)

    async def read(self):
        data = await parse_data(self._reader, **self._kwargs)

        self._url = data.url
        self._args = data.args
        self._method = data.method
        self._http_version = data.http_version
        self._headers = data.headers
        self._data = data.data

        self._real_ip = (
            self.headers['x-from-y']
            if (
                'x-from-y' in self.headers
            ) and (
                self.cfg.believe_x_from_y
            ) else
            self._source_ip
        )
        self._send = False
        self._callback = {
            'before_send': [],
            'after_send': [],
        }
        self._initialized = True

    def get_rw(self):
        return (self._reader, self._writer)

    @property
    def url(self):
        return self._url

    @property
    def args(self):
        return self._args

    @property
    def method(self):
        return self._method

    @property
    def http_version(self):
        return self._http_version

    @property
    def headers(self):
        return self._headers

    @property
    def data(self):
        return self._data

    @property
    def ip(self):
        return self._real_ip

    @property
    def ssl(self):
        return self._ssl

    async def send(self, resp):
        try:
            res = resp.export()
            self._writer.write(res)

            f, args = '{} {} {}', (resp.code, self.url, self.args)
            if self.cfg.request_header in self._headers:
                f = ''.join(['({}) ', f])
                args = (self._headers[self.cfg.request_header], *args)

            await self.logger.info(f, *args)

            await stats.add(key=f'aeon-{resp.code // 100}xx')

            await self._writer.drain()
        except (BrokenPipeError, IOError) as e:
            await self.logger.warning(f'pipe error: {e}')
            self.keep_alive = False
        except Exception as e:
            await self.logger.exception(f'send response: {e}')
            self.keep_alive = False

    async def upgrade_to_ws(self, target, **kwargs):
        if not issubclass(target, WSHandler) and not isinstance(target, WSHandler):
            raise TypeError(f'target ({target}) must be subclass / instance of WSHandler')
        try:
            await stats.add('ws_connections')
            await (
                target
                if isinstance(target, WSHandler) else
                target(self, **kwargs)
            ).mainloop()
        finally:
            await stats.add('ws_connections', -1)

    def is_local(self):
        """
            return True if IP is private
            like 'localhost' or '192.168.*.*'
        """
        return is_local_ip(self.ip)
