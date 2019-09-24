import asyncio
import unittest

from k2.aeon import Aeon, SiteModule, Response


class SimpleSiteModule(SiteModule):
    async def handle(self, request):
        return Response(
            data='{method}: url={url},args={args},data={data},headers={headers}'.format(
                method=request.method,
                url=request.url,
                args=str(request.args),
                data=str(request.data),
                headers=str(request.headers),
            ),
            code=200,
        )


LOOP = asyncio.get_event_loop()


class TestSM(unittest.TestCase):
    def setUp(self):
        self.aeon = Aeon(
            namespace={
                r'^/': SimpleSiteModule(),
                r'^/not_found/': Response(code=404),
            },
        )

    def request(
        self,
        url,
        headers=None,
        args=None,
        data=None,
        method='GET',
        http_version='HTTP/1.1',
        code=200,
    ):
        resp = LOOP.run_until_complete(self.aeon.emulate_request(url, headers, args, data, method, http_version))
        self.assertEqual(resp.code, code)
        data = '{method}: url={url},args={args},data={data},headers={headers}'.format(
            method=method,
            url=url,
            args=str(args or {}),
            data=str(data or b''),
            headers=str(headers or {}),
        )
        if 200 <= resp.code < 300:
            self.assertEqual(resp.data, data)
        return resp

    def test_url(self):
        self.request('/abc')

    def test_code(self):
        self.request('/not_found/', code=404)

    def test_method(self):
        self.request('/', method='POST')

    def test_args(self):
        self.request('/', args={'a': 123})

    def test_data(self):
        self.request('/', data='-- Some Data --')

    def test_headers(self):
        self.request('/', headers={'x-test-header': 'test-value; ???'})
