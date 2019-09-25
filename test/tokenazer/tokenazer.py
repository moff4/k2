import time
import asyncio
import unittest

from k2.tokenazer import Tokenazer

LOOP = asyncio.get_event_loop()


async def f():
    await asyncio.sleep(10)


class TestTokenazer(unittest.TestCase):
    def setUp(self):
        self.tokenazer = Tokenazer(secret=('7' * 32).encode())

    def test_valid_cookie(self):
        cookie = self.tokenazer.generate_cookie(user_id='ABC')
        result = LOOP.run_until_complete(self.tokenazer.valid_cookie(cookie))
        self.assertNotEqual(result, None)
        self.assertEqual(
            result,
            {
                'uid': 'ABC',
                'exp': None,
                'create': int(time.time())
            }
        )

    def test_valid_cookie_with_exp(self):
        cookie = self.tokenazer.generate_cookie(user_id='ABC', expires=10)
        result = LOOP.run_until_complete(self.tokenazer.valid_cookie(cookie))
        self.assertNotEqual(result, None)
        self.assertEqual(
            result,
            {
                'uid': 'ABC',
                'exp': 10,
                'create': int(time.time())
            }
        )
