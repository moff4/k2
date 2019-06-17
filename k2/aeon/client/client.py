#!/usr/bin/env python3

from .base import BaseHTTPSession


class ClientSession(BaseHTTPSession):

    defaults = {
        'max_rederict_count': 8,
    }

    async def _request(self, method, url, *a, **b):
        unallow_rederict = b.pop('unallow_rederict', False)
        for i in range(self.cfg.max_rederict_count):
            res = await super()._request(method=method, url=url, *a, **b)
            await self._parse_cookie(res)
            if res and res.code in {301, 302, 303, 307, 308} and not unallow_rederict:
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
                            options.append(pr.strip())
                res.add_cookie(
                    name=key,
                    value=value,
                    *options,
                    **kwoptions,
                )
        except Exception as e:
            await self._logger.exception('parse-cookie:')