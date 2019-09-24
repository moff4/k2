import asyncio
import unittest

from k2.aeon.exceptions import AeonResponse
from k2.aeon.parser import parse_data

LOOP = asyncio.get_event_loop()


class Reader:
    def __init__(self, data):
        self._data = data if isinstance(data, bytes) else data.encode()

    def __iter__(self):
        return self

    def __next__(self):
        return self._data.pop(0)

    def at_eof(self):
        return not self._data

    async def read(self, i=None):
        i = i or len(self._data)
        data = self._data[:i]
        self._data = self._data[i:]
        return data


class TestParser(unittest.TestCase):
    def do_test(self, data, result, error=True, code=None, **kwargs):
        try:
            data = LOOP.run_until_complete(parse_data(Reader(data), **kwargs))
        except AeonResponse as e:
            self.assertEqual(e.code, code)
        else:
            if error:
                self.assertEqual(data, result)
            else:
                self.assertNotEqual(data, result)
            return data

    def test_protocol_ok(self):
        traffic = '\r\n'.join(
            [
                r'GET   /path/to/page.html    HTTP/1.1',
                r'Host:127.0.0.1',
                r'Connection:     keep-alive',
                r'X-SoMe-RaNdOm-CaSe: HeAdEr',
                r'x-smth: %41%20%42',
                r'Content-Length: 8',
                r'',
                r'ABCDEFGH',
                r'',
            ]
        )
        data = {
            'url': '/path/to/page.html',
            'args': {},
            'headers': {
                'host': '127.0.0.1',
                'connection': 'keep-alive',
                'x-some-random-case': 'HeAdEr',
                'x-smth': 'A B',
                'content-length': '8',
            },
            'data': b'ABCDEFGH',
            'http_version': 'HTTP/1.1',
            'method': 'GET',
        }
        self.do_test(traffic, data)

    def test_protocol_fail_1(self):
        traffic = '\r\n'.join(
            [
                r'GET/ HTTP/1.1',
                r'Host: 127.0.0.1',
                r'Connection: keep-alive',
                r''
            ]
        )
        self.do_test(traffic, {}, code=405)

    def test_protocol_fail_2(self):
        traffic = '\r\n'.join(
            [
                r'GET /HTTP/1.1',
                r'Host: 127.0.0.1',
                r''
            ]
        )
        self.do_test(traffic, {}, code=418)

    def test_protocol_fail_3(self):
        traffic = '\r\n'.join(
            [
                r'GET / HTTP/1.1',
                r'Host 127.0.0.1',
                r''
            ]
        )
        self.do_test(traffic, {}, code=400)

    def test_protocol_fail_4(self):
        traffic = '\r\n'.join(
            [
                r'GET / HTTP/1.1',
                r'Host: 127.0.0.1',
                r''
            ]
        )
        self.do_test(traffic, {}, code=413, max_header_length=7)

    def test_protocol_fail_5(self):
        traffic = '\r\n'.join(
            [
                r'GET / HTTP/1.1',
                r'Host: 127.0.0.1',
                r'Connection: keep-alive',
                r'x-smth: abc',
                r'x-smth-2: def',
                r''
            ]
        )
        self.do_test(traffic, {}, code=400, max_header_count=3)

    def test_protocol_fail_6(self):
        traffic = '\r\n'.join(
            [
                r'GET / HTTP/1.1',
                r'content-length: 8',
                r'',
                r'ABCDEFGH',
                r'',
            ]
        )
        self.do_test(traffic, {}, code=413, max_data_length=3)

    def test_protocol_fail_7(self):
        traffic = '\r\n'.join(
            [
                r'GET /abc/ HTTP/1.1',
                r'content-length: 8',
                r'',
                r'ABCDEFGH',
                r'',
            ]
        )
        self.do_test(traffic, {}, code=414, max_uri_length=3)

    def test_protocol_fail_8(self):
        traffic = '\r\n'.join(
            [
                r'GET /abc/ HTTP/1.1',
                r'content-length: 8',
                r'',
                r'ABCDEFGH',
                r'',
            ]
        )
        self.do_test(traffic, {}, code=405, allowed_methods=set())

    def test_protocol_fail_9(self):
        traffic = '\r\n'.join(
            [
                r'GET /abc/ HTTP/1.1',
                r'content-length: 8',
                r'',
                r'ABCDEFGH',
                r'',
            ]
        )
        self.do_test(traffic, {}, code=418, allowed_http_version=set())
