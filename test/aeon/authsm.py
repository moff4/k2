import asyncio
import unittest


from k2.aeon import (
    Aeon,
    Response,
)
from k2.aeon.sitemodules import AuthSM


class AuthSiteModule(AuthSM):
    user_token_map = {
        'testuser': 'testtoken',
    }

    def authorizator(self, request, **args):
        # Valid if passed token in headers
        if 'test-token' != request.headers.get('x-auth'):
            return False
        if request.url != '/':
            # And valid if passed token as url params
            if request.args.get('token') != self.user_token_map.get(args['username']):
                return False
        return True

    async def get(self, request, **args):
        return Response(data='ok')


LOOP = asyncio.get_event_loop()


class TestAuthSM(unittest.TestCase):
    def setUp(self):
        self.aeon = Aeon(
            namespace={
                r'^/$': AuthSiteModule(),
                r'^/(?P<username>\w+)/$': AuthSiteModule(),
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
        if 200 <= resp.code < 300:
            self.assertEqual(resp.data, 'ok')
        return resp

    def test_ok(self):
        self.request(
            '/',
            headers={
                'x-auth': 'test-token',
            }
        )

    def test_fail(self):
        self.request(
            '/',
            headers={
                'x-auth': 'not-valid-test-token',
            },
            code=403,
        )

    def test_params_ok(self):
        self.request(
            '/testuser/',
            args={
                'token': 'testtoken',
            },
            headers={
                'x-auth': 'test-token',
            },
        )

    def test_params_fail_1(self):
        self.request(
            '/testuser/',
            args={
                'token': 'testuser'
            },
            headers={
                'x-auth': 'not-valid-test-token',
            },
            code=403,
        )

    def test_params_fail_2(self):
        self.request(
            '/unknownuser/',
            args={
                'token': 'testtoken'
            },
            headers={
                'x-auth': 'test-token',
            },
            code=403,
        )

    def test_params_fail_3(self):
        self.request(
            '/unknownuser/',
            args={
                'token': 'invalidtoken'
            },
            headers={
                'x-auth': 'test-token',
            },
            code=403,
        )
