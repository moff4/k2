import unittest

from k2.utils.autocfg import parse_env


class TestParseEnv(unittest.TestCase):
    def test_simple(self):
        res = parse_env({'aeon.protocol.method': 'smth'})
        self.assertEqual(res, {'aeon': {'protocol': {'method': 'smth'}}})

    def test_complex(self):
        res = parse_env(
            {
                'aeon.protocol.method': 'smth',
                'aeon.protocol.version': 123,
                'aeon.ws.timeout': 3.1415,
                'a': 11,
                'b.c': 1123,
            },
        )
        self.assertEqual(
            res,
            {
                'aeon': {
                    'protocol': {
                        'method': 'smth',
                        'version': 123,
                    },
                    'ws': {
                        'timeout': 3.1415,
                    }
                },
                'a': 11,
                'b': {
                    'c': 1123,
                }
            }
        )


if __name__ == '__main__':
    unittest.main()
