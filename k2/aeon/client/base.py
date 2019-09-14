#!/usr/bin/env python3

import asyncio
from os import urandom
from binascii import hexlify

try:
    from ujson import dumps
except ImportError:
    from json import dumps

from urllib.parse import (
    quote,
    quote_from_bytes,
    urlencode,
)


from k2.utils.autocfg import AutoCFG
from k2.utils.http import HTTP_CODE_MSG
from k2.aeon.parser import parse_response_data
from k2.logger import (
    new_channel,
    get_channel,
    delete_channel,
)


ClientLogger = new_channel(
    key='aeon-client',
    parent=get_channel('aeon') or get_channel('base_logger'),
)


class BaseHTTPSession:

    defaults = {
        'timeout': None,
    }

    def __init__(self, host, port, ssl=False, limit=None, loop=None, **kwargs):
        self._conn_args = {
            'host': host,
            'port': port,
            'ssl': ssl,
            **{
                k: v
                for k, v in kwargs.items()
                if k not in {'timeout'}
            },
        }
        if limit:
            self._conn_args['limit'] = limit
        if loop:
            self._conn_args['loop'] = loop

        self._rd = None
        self._wr = None
        self.cfg = AutoCFG(kwargs).update_missing(self.defaults)
        self._logger = None

    async def __aenter__(self):
        await self._open()
        self._logger = new_channel(
            key=f'aeon-client-{hexlify(urandom(2)).decode()}',
            parent=ClientLogger,
        )
        return self

    async def __aexit__(self, ex_type, ex_value, traceback):
        await self._close()
        if self._logger:
            delete_channel(self._logger.cfg.key)
        if ex_value:
            raise ex_value

    async def _open(self):
        self._rd, self._wr = await asyncio.open_connection(
            **self._conn_args
        )

    async def _close(self):
        await self._wr.drain()
        self._wr.close()
        self._rd = None
        self._wr = None

    async def _request(self, method, url, params=None, data=None, json=None, headers=None, **kwargs):
        headers = AutoCFG(
            headers or {},
            key_modifier=lambda x: x.lower(),
        )
        params = params or {}
        headers.update_missing(
            {
                'Host': self._conn_args['host'],
                'User-Agent': 'AeonClient/1.0',
                # FIXME
                # Cannot read data as Content-Length not passed
                # 'Accept-Encoding': 'gzip',
            }
        )
        if not data and json:
            data = dumps(json)
            headers.update_missing(
                {
                    'Content-Type': 'application/json',
                }
            )
        elif not data and method in {'POST', 'PUT', 'DELETE'} and params:
            data = urlencode(params)
            params = {}
        if data:
            if isinstance(data, str):
                data = data.encode()
            headers.update_missing(
                {
                    'Content-Length': len(data),
                }
            )
        await self._logger.debug(
            'making request: {method} {host}:{port}{url} ? {params}',
            method=method,
            host=self._conn_args['host'],
            port=self._conn_args['port'],
            url=url,
            params=params,
        )
        self._wr.write(
            b'\r\n'.join(
                [
                    '{method} {url}{params} HTTP/1.1'.format(
                        method=method,
                        url=url,
                        params=(
                            ''.join(
                                [
                                    '?',
                                    urlencode(params),
                                ]
                            )
                            if params else
                            ''
                        ),
                    ).encode(),
                ] + (
                    [
                        f'{k}: {quote_from_bytes(v) if isinstance(v, bytes) else quote(str(v))}'.encode()
                        for k, v in headers.items()
                    ] if headers else
                    []
                ) + (
                    [
                        b'',
                        data,
                    ]
                    if data else
                    [
                        b'',
                        b'',
                    ]
                )
            )
        )
        await self._wr.drain()
        return await asyncio.wait_for(
            self._read_answer(),
            timeout=kwargs.get('timeout') or self.cfg.timeout,
        )

    async def _read_answer(self):
        try:
            res = await parse_response_data(self._rd, **self.cfg)
            await self._logger.debug(f'''result: {res.code} {HTTP_CODE_MSG.get(res.code, 'Unknown status')}''')
            return res
        except ValueError:
            await self._logger.exception('Response error:')

    async def get(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('GET', url=url, params=params, data=data, json=json, headers=headers, *a, **b)

    async def post(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('POST', url=url, params=params, data=data, json=json, headers=headers, *a, **b)

    async def head(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('HEAD', url=url, params=params, data=data, json=json, headers=headers, *a, **b)

    async def put(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('PUT', url=url, params=params, data=data, json=json, headers=headers, *a, **b)

    async def delete(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('DELETE', url=url, params=params, data=data, json=json, headers=headers, *a, **b)

    async def options(self, url, params=None, data=None, json=None, headers=None, *a, **b):
        return await self._request('OPTIONS', url=url, params=params, data=data, json=json, headers=headers, *a, **b)
