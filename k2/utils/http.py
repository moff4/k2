#!/usr/bin/etc python3

PRIVETE_IP = set(
    {'10.', '192.168.', '0.0.0.0', '127.0.0.'}.union(
        {('100.%s.' % i) for i in range(64, 128)}
    ).union(
        {('172.%s.' % i) for i in range(16, 32)}
    )
)

HTTP_CODE_MSG = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    206: 'Partial Content',
    301: 'Moved Permanently',
    304: 'Not Modified',
    307: 'Temporary Redirect',
    308: 'Permanent Rederict',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not found',
    405: 'Method Not Allowed',
    409: 'Conflict',
    411: 'Length Required',
    418: 'I’m a teapot',
    424: 'Failed Dependency',
    429: 'Too Many Requests',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    504: 'Gateway Timeout',
}

HTTP_METHODS = [
    'GET',
    'POST',
    'HEAD',
    'PUT',
    'DELETE',
]
HTTP_VERSIONS = [
    'HTTP/1.1',
]

NOT_FOUND = '''
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL was not found on this kek-server.</p>
</body></html>
'''
SMTH_HAPPENED = '''
<html><head>
<title>500 Smth happened</title>
</head><body>
<h1>Smth happened</h1>
<p>The requested URL found error this kek-server.</p>
</body></html>
'''

DIR_TEMPLATE = '''
<html><head>
<title>kek-server</title>
</head><body>
<h1>{url}</h1>
<ul>
{cells}
</ul>
</body></html>
'''
DIR_CELL_TEMPLATE = '''
<li><a href="{url}{filename}">{filename}</a></li>
'''

CONTENT_HTML = {'Content-type': 'text/html; charset=utf-8'}
CONTENT_JS = {'Content-type': 'application/javascript; charset=utf-8'}
CONTENT_JSON = {'Content-type': 'text/json; charset=utf-8'}

STANDART_HEADERS = {
    'Server': 'kek-server',
    'Content-type': 'text/html; charset=utf-8',
    'Accept-Ranges': 'bytes',
}


MAX_DATA_LEN = 8 * (2 ** 20)
MAX_HEADER_COUNT = 64
MAX_HEADER_LEN = 2 ** 10


async def readln(reader, max_len=None, ignore_zeros=False):
    st = []
    a = True
    while a:
        a = await reader.read(1)
        if (not st and (not ignore_zeros or a[0] >= 32)) or st:
            if a == b'\n':
                break
            if a and a != b'\r':
                st.append(a[0])
                if max_len is not None and len(st) > max_len:
                    raise ValueError('Header is too long')
    return bytes(st)


def Content_type(st) -> str:
    """
        get filename and decide content-type header
        st == req.url
    """
    extra = ''
    st = st.split('.')[-1]
    if st in {'html', 'css', 'txt', 'csv', 'xml', 'js', 'json', 'php', 'md'}:
        type_1 = 'text'
        if st == 'js':
            type_2 = 'javascript'
        elif st == 'md':
            type_2 = 'markdown'
        elif st == 'html':
            type_2 = st
            extra = '; charset=utf-8'
        else:
            type_2 = st

    elif st in {'jpg', 'jpeg', 'png', 'gif', 'tiff'}:
        type_1 = 'image'
        type_2 = st

    elif st in {'mkv', 'avi', 'mp4'}:
        type_1 = 'video'
        if st in {'mp4', 'avi'}:
            type_2 = st
        else:
            type_2 = 'webm'
    else:
        return {'Content-type': 'text/plain'}
    return {'Content-type': '{}/{}{}'.format(type_1, type_2, extra)}


def is_local_ip(addr) -> bool:
    return any(
        map(
            lambda x: addr.startswith(x),
            PRIVETE_IP,
        )
    )
