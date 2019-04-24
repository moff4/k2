#!/usr/bin/env python3

from k2.aeon.parser import parse_data
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    is_local_ip
)


class Request:
    """
        class for each request
        must be args:
            addr - tuple (ip,port)
            reader - io stream
            writer - io stream
        kwargs:
            id - unique id of the request (default: 0)
            believe_x_from_y - bool: if True source ip = X-From-Y (default: False)
            cache_min - int - seconds for HTTP header 'Cache-Control: max-age'
            max_header_length - max length of any HTTP-header (default: 1024B)
            max_header_count - max amount of HTTP-headers (default: 64)
            max_data_length - max length of data (default: 8MB)
            allowed_methods -  set/list of allowed HTTP methods (default: {'GET', 'POST', 'HEAD', 'PUT', 'DELETE'})
            allowed_http_version - set/list of allowed HTTP version (default: {'HTTP/1.1'})
    """

    name = 'request'
    defaults = {
        'id': 0,
        'believe_x_from_y': False,
        'cache_min': 120,
    }

    def __init__(self, addr, reader, writer, **kwargs):
        self.cfg = AutoCFG(self.defaults).update_fields(kwargs)
        self._kwargs = kwargs
        self._addr = addr
        self._reader = reader
        self._writer = writer
        self._source_ip = self._addr[0]
        self.port = self._addr[1]

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
        self._ssl = False
        self._send = False
        self._callback = {
            'before_send': [],
            'after_send': [],
        }

    def __call__(self, st='', _type='notify'):
        """
            local log function
            extra save request-id
        """
        self.log(st='[{id}] {st}'.format(id=self.cfg['id'], st=st), _type=_type)

    # ==========================================================================
    #                             USER API
    # ==========================================================================

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

    @ssl.setter
    def ssl(self, value):
        self._ssl = value

    async def send(self, resp):
        res = resp.export()
        print('res: %s' % res)
        self._writer.write(res)
        await self._writer.drain()

    def is_local(self):
        """
            return True if IP is private
            like 'localhost' or '192.168.*.*'
        """
        return is_local_ip(self.ip)
