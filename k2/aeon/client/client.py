#!/usr/bin/env python3

from urllib.parse import urlparse

from .base import BaseHTTPSession


class ClientSession(BaseHTTPSession):

    defaults = BaseHTTPSession.defaults
    defaults.update(
        {
            'max_rederict_count': 8,
        }
    )

    async def _request(self, method, url, *a, **b):
        allow_redirects = b.pop('allow_redirects', True)
        for i in range(self.cfg.max_rederict_count):
            res = await super()._request(method=method, url=url, *a, **b)
            await self._parse_cookie(res)
            if res and res.code in {301, 302, 303, 307, 308} and allow_redirects:
                url = res.headers.get('location')
                if url is None:
                    return res
                method = 'GET' if res.code == 303 else method
            else:
                return res

    async def _parse_cookie(self, res):
        try:
            if 'set-cookie' in res.headers:
                for cookie_str in res.headers['set-cookie'].split(','):
                    options = []
                    kwoptions = {}
                    kv, *pr = cookie_str.split(';')
                    key, value = [i.strip() for i in kv.split('=')]
                    for i in pr:
                        if '=' in pr:
                            pr_k, pr_v = [i.strip() for i in kv.split('=')]
                            kwoptions[pr_k] = pr_v
                        else:
                            options.append(i.strip())
                res.add_cookie(
                    key,
                    value,
                    *options,
                    **kwoptions,
                )
                res.headers.pop('set-cookie')
        except Exception:
            await self._logger.exception('parse-cookie:')

async def _request(method, url, params=None, data=None, json=None, headers=None, *a, **b):
    url = urlparse(url)
    host, port = (
        url.netloc.split(':')
        if ':' in url.netloc else
        (
            url.netloc,
            80
            if url.scheme == 'http' else
            443,
        )
    )
    async with ClientSession(
        host=host,
        port=int(port),
        ssl=url.scheme == 'https',
        *a,
        **b,
    ) as session:
        return await session._request(
            url.path,
            params=params,
            data=data,
            json=json,
            headers=headers,
            *a,
            **b,
        )

async def get(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='GET',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )

async def post(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='POST',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )

async def head(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='HEAD',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )

async def put(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='PUT',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )

async def delete(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='DELETE',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )

async def options(url, params=None, data=None, json=None, headers=None, *a, **b):
    return await _request(
        method='OPTIONS',
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        *a,
        **b,
    )
