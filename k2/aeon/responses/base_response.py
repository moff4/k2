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

    def __init__(self, data=None, headers=None, code=200):
        if data is not None and not isinstance(data, (str, bytes)):
            raise TypeError('data must be str or bytes')

        if headers is not None and not isinstance(headers, dict):
            raise TypeError('headers must be dict')

        if not isinstance(code, int):
            raise TypeError('code must be int')

        # response data
        self._data = data or b''
        # dict of headers: {'Content-Type': 'text/html'}
        self._headers = AutoCFG() if headers is None else AutoCFG(headers)
        # HTTP status code: 200
        self._code = code
        # list of Set-Cookie header values: ['uid=123; HttpOnly', 'session_id=abc; Secure']
        self._cookies = []
        self._http_version = 'HTTP/1.1'

    def _extra_prepare_data(self):
        return self.data

    @property
    def code(self) -> int:
        return self._code

    @code.setter
    def code(self, code):
        self._code = code

    @property
    def http_version(self) -> str:
        return self._http_version

    @http_version.setter
    def http_version(self, value):
        self._http_version = value

    @property
    def data(self) -> bytes:
        return self._data

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
        self._cookies.append(
            '; '.join(
                [
                    '{}={}'.format(name, quote(str(value)))
                ] + [
                    '{}={}'.format(key, quote(str(value)))
                    for key, value in kwoptions.items()
                ] + list(
                    options
                )
            )
        )

    def export(self) -> str:
        data = self._extra_prepare_data()
        data = data.encode() if isinstance(data, str) else data
        headers = AutoCFG(STANDART_HEADERS).update_fields(self._headers)
        headers.update({'Content-Length': len(data)})
        return b''.join(
            [
                '\r\n'.join(
                    [
                        '{http_version} {code} {code_msg}'.format(
                            http_version=self.http_version,
                            code=204 if len(data) <= 0 and self.code in {200, 201} else self.code,
                            code_msg=HTTP_CODE_MSG[self.code]
                        ),
                    ] + [
                        ''.join([i, ': ', str(headers[i])])
                        for i in filter(
                            lambda x: x,
                            headers,
                        )
                    ] + [
                        'Set-Cookie: {}'.format(k)
                        for k in self._cookies
                    ] + ['\r\n'],
                ).encode(),
                data
            ]
        )
