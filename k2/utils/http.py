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
    102: 'Proccessing',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    206: 'Partial Content',
    207: 'Multi-Status',
    208: 'Already Reported',
    226: 'IM used',
    301: 'Moved Permanently',
    302: 'Moved Temporary',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: 'Reserved',
    307: 'Temporary Redirect',
    308: 'Permanent Rederict',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Payload Too Large',
    414: 'URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'I’m a teapot',
    419: 'Authentication Timeout',
    421: 'Misdirected Request',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    449: 'Retry With',
    451: 'Unavailable For Legal Reasons',
    499: 'Client Closed Request',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    509: 'Bandwidth Limit Exceeded',
    510: 'Not Extended',
    511: 'Network Authentication Required',
    520: 'Unknown Error',
    521: 'Web Server Is Down',
    522: 'Connection Timed Out',
    523: 'Origin Is Unreachable',
    524: 'A Timeout Occurred',
    525: 'SSL Handshake Failed',
    526: 'Invalid SSL Certificate',
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
MAX_URI_LENGTH = 256


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
