#!/usr/bin/env python3

from urllib.parse import (
    urlparse,
    parse_qs,
)

from k2.aeon.exceptions import AeonResponse
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    MAX_DATA_LEN,
    MAX_HEADER_COUNT,
    MAX_HEADER_LEN,
    MAX_URI_LENGTH,
    readln,
)


async def parse_data(reader, **kwargs):
    """
        take io stream and cfg and parse HTTP headers
        return dict of attributes/headers/url/args
    """
    __defaults = {
        'max_header_length': MAX_HEADER_LEN,
        'max_header_count': MAX_HEADER_COUNT,
        'max_data_length': MAX_DATA_LEN,
        'max_uri_length': MAX_URI_LENGTH,
        'allowed_methods': {'GET', 'HEAD', 'POST', 'PUT', 'DELETE'},
        'allowed_http_version': {'HTTP/1.1'},
    }
    cfg = AutoCFG(__defaults).update_fields(kwargs)
    req = AutoCFG(
        {
            'url': b'',
            'args': {},
            'method': b'',
            'http_version': b'',
            'headers': {},
            'data': b'',
        }
    )
    st = await readln(
        reader,
        max_len=cfg.max_uri_length + 12,
        ignore_zeros=True,
        exception=AeonResponse('URI too long', code=414),
    )
    tmp = []
    i = 0
    while len(st) > i and st[i] > 32:
        tmp.append(st[i])
        i += 1
    st = st[i + 1:].strip()

    req.method = bytes(tmp).decode()
    if not req.method:
        raise AeonResponse('Empty method field', code=400)
    elif req.method not in cfg.allowed_methods:
        raise AeonResponse('Unexpected method "{}"'.format(req.method), code=405)

    tmp = []
    for i in st:
        if i > 32:
            tmp.append(i)
        else:
            break
    parsed_url = urlparse(bytes(tmp).decode('utf-8'))
    req.url = parsed_url.path
    args = parse_qs(parsed_url.query)
    req.args = {k: args[k][0] for k in args if args[k]}
    st = st[len(tmp):].strip()

    tmp = []
    i = 0
    while len(st) > i and st[i] > 32:
        tmp.append(st[i])
        i += 1
    req.http_version = bytes(tmp).decode('utf-8')
    if req.http_version not in cfg.allowed_http_version:
        raise AeonResponse('Unexpected HTTP version: {}'.format(req.http_version), code=418)

    err_413 = AeonResponse(code=413)
    while True:
        st = await readln(
            reader,
            max_len=cfg.max_header_length,
            exception=err_413
        )
        if not st:
            break

        st = st.decode('utf-8').split(':')
        key = st[0].lower()
        if key in req.headers:
            raise AeonResponse('Got 2 same headers ({key})'.format(key=key), code=400)
        elif len(req.headers) >= cfg.max_header_count:
            raise AeonResponse('Too many headers', code=400)
        req.headers[key] = ':'.join(st[1:]).strip()

    if any(map(lambda x: x in req.url, {'..', '//'})):
        raise AeonResponse('Unallowed req: {url}'.format(**req), code=400)

    if 'content-length' in req.headers:
        _len = int(req.headers['content-length'])
        if _len >= cfg.max_data_length:
            raise AeonResponse('Too much data', code=413)
        req.data = reader.recv(_len)
    return req
