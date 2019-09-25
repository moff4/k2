
import asyncio
import unittest

from k2.tokenazer import Tokenazer

LOOP = asyncio.get_event_loop()


class TestTokenazer(unittest.TestCase):
    def setUp(self):
        self.tokenazer = Tokenazer(secret=('7' * 32).encode())

    def test_valid_cookie(self):
        return
        # FIXME
        # smth strange
        # not yet fixed
        cookie = self.tokenazer.generate_cookie(user_id='ABC', ip='127.0.0.122', rights={'root', 'admin', 'cool man'})
        result = LOOP.run_until_complete(self.tokenazer.valid_cookie(cookie))
        self.assertNotEqual(result, None)
        self.assertEqual(
            result,
            {
                'user_id': 'ABC',
                'ip': '127.0.0.122',
                'rights': {'root', 'admin', 'cool man'},
            }
        )
