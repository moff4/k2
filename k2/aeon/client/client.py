#!/usr/bin/env python3

from urllib.parse import urlparse

from .base import BaseHTTPSession

from k2.utils.autocfg import AutoCFG


class ClientSession(BaseHTTPSession):

    defaults = BaseHTTPSession.defaults
    defaults.update(
        {
            'max_rederict_count': 8,
        }
    )

    async def _change_conn(self, host, port, ssl=False):
        await self._close()
        self._conn_args.update(
            {
                'host': host,
                'port': port,
                'ssl': ssl,
            },
        )
        await self._open()

    async def _request(self, method, url, *a, **b):
        allow_redirects = b.pop('allow_redirects', True)
        for _ in range(self.cfg.max_rederict_count):
            await self._parse_cookie(res := await super()._request(method=method, url=url, *a, **b))
            if res and res.code in {301, 302, 303, 307, 308} and allow_redirects:
                if (url := res.headers.get('location')) is None:
                    return res
                await self._logger.debug('rederict to {}', url)
                if url.startswith('http://') or url.startswith('https://'):
                    host, port = (
                        new_url.netloc.split(':')
                        if ':' in (new_url := urlparse(url)).netloc else
                        (
                            new_url.netloc,
                            80
                            if new_url.scheme == 'http' else
                            443,
                        )
                    )
                    await self._change_conn(
                        host=host,
                        port=int(port),
                        ssl=new_url.scheme == 'https',
                    )
                method = 'GET' if res.code == 303 else method
            else:
                return res

    async def _parse_cookie(self, res):
        try:
            if 'set-cookie' in res.headers:
                cookie_strs = res.headers['set-cookie'].split(',')
                i = 0
                while i < len(cookie_strs):
                    options = []
                    kwoptions = {}
                    kv, *pr = cookie_strs[i].split(';')
                    key, value = [k.strip() for k in kv.split('=')]
                    while pr:
                        if '=' in (j := pr.pop(0)):
                            pr_k, pr_v = [k.strip() for k in j.split('=')]
                            if pr_k == 'expires':
                                i += 1
                                j = (pr_next := cookie_strs[i].split(';')).pop(0)
                                pr.extend(pr_next)
                                pr_v = ','.join([pr_v, j])
                            kwoptions[pr_k] = pr_v
                        else:
                            options.append(j.strip())
                    i += 1
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
    headers = AutoCFG(headers or {}).update_missing(
        {
            'Connection': 'close',
        }
    )
    async with ClientSession(
        host=host,
        port=int(port),
        ssl=url.scheme == 'https',
        *a,
        **b,
    ) as session:
        b.pop('timeout', None)
        return await session._request(
            method=method,
            url=url.path or '/',
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
