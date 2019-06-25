#!/usr/bin/env python3

from urllib.parse import quote

from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    HTTP_CODE_MSG,
    STANDART_HEADERS,
)


class Response:
    """
        basic class for response
    """

    def __init__(self, data=None, headers=None, code=200, cookies=None, http_version='HTTP/1.1'):
        if data is not None and not isinstance(data, (str, bytes)):
            raise TypeError('data must be str or bytes')

        if headers is not None and not isinstance(headers, dict):
            raise TypeError('headers must be dict')

        if not isinstance(code, int):
            raise TypeError('code must be int')

        # response data
        self._data = data or b''
        # dict of headers: {'Content-Type': 'text/html'}
        self._headers = AutoCFG(headers or {}, key_modifier=lambda x: x.lower())
        # HTTP status code: 200
        self._code = code
        # dict of dicts for Set-Cookie header:
        # {'uid': {'value': '123', 'flags':['HttpOnly'], 'properties': {'Path': '/'}}
        self._cookies = AutoCFG()
        if cookies:
            for ck in cookies:
                self.add_cookie(**ck)
        self._http_version = http_version

    async def _extra_prepare_data(self):
        return self.data

    async def _cache_n_zip(self, data):
        return data

    def __str__(self):
        return f'<Response: {self._code} {HTTP_CODE_MSG[self._code]}>'

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code):
        if code not in HTTP_CODE_MSG:
            raise ValueError('Code must be in k2.utils.http.HTTP_CODE_MSG')
        self._code = code

    @property
    def http_version(self) -> str:
        return self._http_version

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def cookies(self) -> AutoCFG:
        return self._cookies

    @property
    def headers(self) -> AutoCFG:
        return self._headers

    @data.setter
    def data(self, data):
        self._data = b'' if data is None else (data.encode() if isinstance(data, str) else data)

    def add_headers(self, *args, **kwargs):
        if any([not isinstance(i, (dict, tuple)) for i in args]):
            raise TypeError('HTTP-header must be tuple of dict')

        if any([not isinstance(kwargs[i], str) for i in kwargs]):
            raise TypeError('HTTP-header value must be string')

        self._headers.update(*args, **kwargs)

    def add_cookie(self, name, value, *options, **kwoptions):
        """
            name - cookie name
            value - value of cookie
            options - boolean properties like HttpOnly and Secure
            kwoptions - kev-value properties like Max-Age and Domain
        """
        self._cookies[name] = {
            'value': value,
            'flags': set(options),
            'properties': AutoCFG(kwoptions)
        }

    async def export(self) -> str:
        data = await self._extra_prepare_data()
        data = data.encode() if isinstance(data, str) else data
        data = await self._cache_n_zip(data)
        headers = self._headers.update_missing(STANDART_HEADERS)
        headers.update({'Content-Length': len(data)})
        return b''.join(
            [
                '\r\n'.join(
                    [
                        f'{self.http_version} '
                        f'{204 if len(data) <= 0 and self.code in {200, 201} else self.code} '
                        f'{HTTP_CODE_MSG[self.code]}',
                    ] + [
                        ''.join([i, ': ', str(headers[i])])
                        for i in filter(
                            lambda x: x,
                            headers,
                        )
                    ] + [
                        'Set-Cookie: {}'.format(
                            '; '.join(
                                [
                                    f'''{name}={quote(self._cookies[name]['value'])}'''
                                ] + [
                                    f'{key}={quote(str(val))}'
                                    for key, val in self._cookies[name]['properties'].items()
                                ] + list(
                                    self._cookies[name]['flags']
                                )
                            )
                        )
                        for name in self._cookies
                    ] + ['\r\n'],
                ).encode(),
                data
            ]
        )
