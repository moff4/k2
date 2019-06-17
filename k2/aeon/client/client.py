#!/usr/bin/env python3
try:
    from ujson import dumps
except ImportError:
    from json import dumps

import asyncio
from urllib.parse import (
    quote,
    quote_from_bytes,
    urlencode,
)


from k2.utils.autocfg import AutoCFG
from k2.aeon.parser import parse_response_data


class BaseClientSession:
    def __init__(self, host, port, ssl=False, limit=None, loop=None, **kwargs):
        self._conn_args = {
            'host': host,
            'port': port,
            'ssl': ssl,
        }
        if limit:
            self._conn_args['limit'] = limit
        if loop:
            self._conn_args['loop'] = loop

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
        self._rd, self._wr = await asyncio.open_connection(
            **self._conn_args
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
        headers = AutoCFG(
            headers or {},
            key_modifier=lambda x: x.lower(),
        )
        headers.update_missing(
            {
                'Host': self._conn_args['host'],
                'User-Agent': 'AeonClient/1.0',
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
            params = None
        if data:
            if isinstance(data, str):
                data = data.encode()
            headers.update_missing(
                {
                    'Content-Length': len(data),
                }
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
        return await self._read_answer()

    async def _read_answer(self):
        return await parse_response_data(self._rd, **self._kwargs)

    async def get(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('GET', url=url, params=params, data=data, json=json, headers=headers)

    async def post(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('POST', url=url, params=params, data=data, json=json, headers=headers)

    async def head(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('HEAD', url=url, params=params, data=data, json=json, headers=headers)

    async def put(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('PUT', url=url, params=params, data=data, json=json, headers=headers)

    async def delete(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('DELETE', url=url, params=params, data=data, json=json, headers=headers)

    async def options(self, url, params=None, data=None, json=None, headers=None):
        return await self._request('OPTIONS', url=url, params=params, data=data, json=json, headers=headers)
