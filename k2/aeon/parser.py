#!/usr/bin/env python3
import os
from urllib.parse import (
    urlparse,
    parse_qs,
    unquote,
)

from k2.aeon.exceptions import AeonResponse
from k2.aeon.responses.client.client import ClientResponse
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    MAX_DATA_LEN,
    MAX_HEADER_COUNT,
    MAX_HEADER_LEN,
    MAX_URI_LENGTH,
    HTTP_METHODS,
    MAX_STATUS_LENGTH,
    readln,
)

PARSE_DATA_DEFAULTS = {
    'max_header_length': MAX_HEADER_LEN,
    'max_header_count': MAX_HEADER_COUNT,
    'max_data_length': MAX_DATA_LEN,
    'max_uri_length': MAX_URI_LENGTH,
    'allowed_methods': HTTP_METHODS,
    'allowed_http_version': {'HTTP/1.1'},
}

PARSE_RESPONSE_DEFAULTS = {
    'max_header_length': MAX_HEADER_LEN,
    'max_header_count': MAX_HEADER_COUNT,
    'max_data_length': MAX_DATA_LEN,
    'max_status_length': MAX_STATUS_LENGTH,
    'expected_http_version': {'HTTP/1.1'},
}


async def parse_data(reader, **kwargs):
    """
        take io stream and cfg and parse HTTP headers
        return dict of attributes/headers/url/args
    """
    cfg = AutoCFG(PARSE_DATA_DEFAULTS).update_fields(kwargs)
    req = AutoCFG(
        {
            'url': b'',
            'args': {},
            'method': b'',
            'http_version': b'',
            'headers': AutoCFG(key_modifier=lambda x: x.lower()),
            'data': b'',
        }
    )
    if reader.at_eof():
        raise RuntimeError('socket was closed')
    if not (st := (
        await readln(
            reader,
            max_len=cfg.max_uri_length + 12,
            ignore_zeros=True,
            exception=AeonResponse('URI too long', code=414),
        )
        ).strip()
    ):
        raise AeonResponse('empty string', code=400, close_conn=True, silent=True)
    i = 0
    while len(st) > i and st[i] > 32:
        i += 1

    req.method = bytes(st[:i]).decode()
    if not req.method:
        raise AeonResponse('Empty method field', code=400, close_conn=True, silent=True)
    elif req.method not in cfg.allowed_methods and '*' not in cfg.allowed_methods:
        raise AeonResponse(f'Unexpected method "{req.method}"', code=405)

    st = st[i:].lstrip()
    i = 0
    while len(st) > i and st[i] > 32:
        i += 1

    req.url = (parsed_url := urlparse(bytes(st[:i]).decode('utf-8'))).path
    req.args = {k: v[0] for k, v in parse_qs(parsed_url.query).items() if v}
    st = st[i:].lstrip()

    i = 0
    while len(st) > i and st[i] > 32:
        i += 1
    req.http_version = bytes(st[:i]).decode('utf-8')
    if req.http_version not in cfg.allowed_http_version:
        raise AeonResponse(f'Unexpected HTTP version: {req.http_version}', code=418, close_conn=True)

    err_413 = AeonResponse(code=413)
    while st := await readln(
        reader,
        max_len=cfg.max_header_length,
        exception=err_413
    ):
        if len(st := st.decode('utf-8').split(':')) < 2:
            raise AeonResponse('Http parse error', code=400)
        if len(req.headers) >= cfg.max_header_count:
            raise AeonResponse('Too many headers', code=400)
        req.headers[key] = (
            ', '.join(
                [
                    req.headers[key],
                    unquote(':'.join(st[1:]).strip()),
                ]
            )
            if (key := st[0].lower()) in req.headers else
            unquote(':'.join(st[1:]).strip())
        )

    if os.path.normpath(req.url).startswith('..'):
        raise AeonResponse(f'Unallowed req: {req.url}', code=400, close_conn=True)

    if 'content-length' in req.headers:
        if (_len := int(req.headers['content-length'])) >= cfg.max_data_length:
            raise AeonResponse('Too much data', code=413)
        buff = []
        length = 0
        while length < _len:
            buff.append(await reader.read(_len - length))
            length += len(buff[-1])
        req.data = b''.join(buff)
    return req


async def parse_response_data(reader, **kwargs):
    """
        take io stream and cfg and parse HTTP headers
        return dict of attributes/headers/url/args
    """
    cfg = AutoCFG(PARSE_RESPONSE_DEFAULTS).update_fields(kwargs)
    if reader.at_eof():
        raise ValueError('socket was closed')

    if not (
        st := (
            await readln(
                reader,
                max_len=cfg.max_status_length,
                ignore_zeros=True,
            )
        ).decode()
    ) or not st.startswith('HTTP/'):
        raise ValueError('Invalid protocol')

    version, code, *_ = st.split()

    if version not in cfg.expected_http_version:
        raise ValueError('unsupported protocol version "{}"'.format(version))

    if not code.isdigit():
        raise ValueError('status code is not integer "{}"'.format(code))

    if not (100 <= (code := int(code)) < 600):
        raise ValueError('Invalid status code')
    headers = AutoCFG(key_modifier=lambda x: x.lower())

    for _ in range(cfg.max_header_count):
        if not (st := (await readln(reader, max_len=cfg.max_header_length)).decode().strip()):
            break

        key, *value = st.split(':')
        if not value:
            raise ValueError('Invalid headers format')
        value = unquote(':'.join(value).strip())
        if (key := key.lower()) in headers:
            headers[key] = ', '.join(
                [
                    headers[key],
                    value,
                ],
            )
        else:
            headers[key] = value

    if st:
        raise ValueError('Too many headers')

    data = []
    if 'content-length' in headers:
        if cfg.max_data_length < (content_length := int(headers['content-length'])):
            raise ValueError('Got unexpectedly much data: {} bytes'.format(content_length))
        step = 2 ** 14
        loaded = 0
        while _l := content_length - loaded:
            data.append(_d := await reader.read(min(step, content_length - loaded)))
            loaded += len(_d)
    return ClientResponse(
        data=b''.join(data),
        headers=headers,
        code=code,
        http_version=version,
    )
