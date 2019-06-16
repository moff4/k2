#!/usr/bin/env python3
try:
    from ujson import dumps
except ImportError:
    from json import dumps

import asyncio
from urllib.parse import (
    quote,
    urlencode,
)


from k2.utils.autocfg import AutoCFG
from k2.aeon.parse import parse_response_data


class ClientSession:
    def __init__(self, host, port, ssl=False, limit=None, loop=None, **kwargs):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.limit = limit
        self.loop = loop
        self._rd = None
        self._wr = None
        self._kwargs = kwargs

    async def __aenter__(self):
        await self._open()
        return self

    async def __aexit__(self, ex_type, ex_value, traceback):
        await self._close()
        if ex_value:
            raise ex_value

    async def _open(self):
        self._rd, self.rw = await asyncio.open_connection(
            host=self.host,
            port=self.port,
            ssl=self.ssl,
            limit=self.limit,
            loop=self.loop,
        )

    async def _close(self):
        self._rd = None
        self._wr = None
        try:
            self.rw.close()
            await self.rw.drain()
        except Exception:
            pass

    async def _request(self, method, url, params=None, data=None, json=None, headers=None):
        if not data and json:
            data = dumps(data)
        if data:
            if isinstance(data, str):
                data = data.encode()
            AutoCFG(headers).update_missing(
                {
                    'Content-Length': len(data),
                    'User-Agent': 'AeonClient/1.0',
                }
            )
        await self._wr.write(
            b'\r\n'.join(
                [
                    '{method} {url} HTTP/1.1'.format(
                        method=method,
                        url=url,
                        params=urlencode(params) if params else '',
                    ).encode(),
                ] + (
                    [
                        f'{k}: {quote(v)}'.encode()
                        for k, v in headers.items()
                    ] if headers else
                    []
                ) + (
                    [
                        b'',
                        data,
                    ]
                    if data else
                    []
                )
            )
        )
        await self._wr.drain()
        return await self._read_answer()

    async def _read_answer(self):
        return await parse_response_data(self._rd, **self._kwargs)

    async def get(self, url, params=None, data=None, json=None):
        return await self._request('GET', url=url, params=params, data=data, json=json)

    async def post(self, url, params=None, data=None, json=None):
        return await self._request('POST', url=url, params=params, data=data, json=json)

    async def head(self, url, params=None, data=None, json=None):
        return await self._request('HEAD', url=url, params=params, data=data, json=json)

    async def put(self, url, params=None, data=None, json=None):
        return await self._request('PUT', url=url, params=params, data=data, json=json)

    async def delete(self, url, params=None, data=None, json=None):
        return await self._request('DELETE', url=url, params=params, data=data, json=json)

    async def options(self, url, params=None, data=None, json=None):
        return await self._request('OPTIONS', url=url, params=params, data=data, json=json)
