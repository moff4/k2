import json
import asyncio
import unittest

from k2.aeon import Aeon
from k2.aeon.sitemodules import RestSM


class RestSiteModule(RestSM):

    def __init__(self):
        self.GET_schema = {
            'type': dict,
            'value': {
                'name': {
                    'type': str,
                },
                'age': {
                    'type': int,
                    'pre_call': lambda x: int(x),
                }
            }
        }
        self.deserializer = json.loads
        self.serializer = json.dumps

    @staticmethod
    def GET_getter(request):
        return request.args

    @staticmethod
    def GET_setter(request, data):
        request.args = data

    async def get(self, request):
        return '{method}: name={name}, age={age}'.format(
            method=request.method,
            name=request.args['name'],
            age=str(request.args['age']),
        )


LOOP = asyncio.get_event_loop()


class TestRestSM(unittest.TestCase):
    def setUp(self):
        self.aeon = Aeon(
            namespace={
                r'^/': RestSiteModule(),
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
        data = json.dumps(
            '{method}: name={name}, age={age}'.format(
                method=method,
                name=args['name'],
                age=str(args['age']),
            )
        )
        if 200 <= resp.code < 300:
            self.assertEqual(resp.data, data)
        return resp

    def test_ok(self):
        self.request(
            '/abc',
            args={
                'name': 'Ivan Petrov',
                'age': '22',
            }
        )

    def test_fail(self):
        self.request(
            '/abc',
            args={
                'name': 'Ivan Petrov',
                'age': 'not-integer',
            },
            code=400,
        )
