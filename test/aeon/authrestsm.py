import json
import asyncio
import unittest

from k2.aeon import Aeon
from k2.aeon.sitemodules import AuthSM, RestSM


class AuthRestSiteModule(AuthSM, RestSM):
    def authorizator(self, request, **args):
        # Valid if passed token in headers
        return 'test-token' == request.headers.get('x-auth')

    GET_schema = {
        'type': dict,
        'value': {
            'user_id': {
                'pre_call': str,
                'type': str,
            }
        }
    }

    async def get(self, request, **args):
        return {
            'response': request.args['user_id'],
        }


LOOP = asyncio.get_event_loop()


class TestAuthRestSM(unittest.TestCase):
    def setUp(self):
        self.aeon = Aeon(
            namespace={
                r'^/$': AuthRestSiteModule(),
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
        return resp

    def test_ok(self):
        resp = self.request(
            '/',
            headers={
                'x-auth': 'test-token',
            },
            args={
                'user_id': '123',
            }
        )
        self.assertEqual(json.loads(resp.data), {'response': '123'})

    def test_auth_fail(self):
        self.request(
            '/',
            headers={
                'x-auth': 'no-valid-token',
            },
            args={
                'user_id': '123',
            },
            code=403
        )

    def test_rest_fail(self):
        self.request(
            '/',
            headers={
                'x-auth': 'test-token',
            },
            args={
                'user': '123',
            },
            code=400
        )
