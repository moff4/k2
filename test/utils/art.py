from os import urandom
import unittest

from k2.utils import art


class AbstractArt:

    def do_test(self, x, m1=None, m2=None, expect=True):
        try:
            z = art.marshal(x, mask=m1)
            y = art.unmarshal(z, mask=m2)
            if expect:
                self.assertEqual(x, y)
            else:
                self.assertNotEqual(x, y)
        except (OverflowError, RuntimeError, ValueError, TypeError):
            self.assertFalse(expect)

    def test_unmask(self):
        for x in self.get_x():
            self.do_test(x)

    def test_mask(self):
        for x in self.get_x():
            mask = urandom(8)
            self.do_test(x, m1=mask, m2=mask)

    def test_mask_1_fail(self):
        for x in self.get_x():
            m1 = urandom(8)
            m2 = urandom(8)
            while m2 == m1:
                m2 = urandom(8)
            self.do_test(x, m1=m1, m2=m2, expect=False)

    def test_mask_1_fail_2(self):
        m1 = urandom(8)
        for x in self.get_x():
            self.do_test(x, m1=m1, m2=None, expect=False)

    def test_mask_2_fail(self):
        m1 = urandom(8)
        m2 = urandom(8)
        while m2 == m1:
            m2 = urandom(8)
        for x in self.get_x():
            self.do_test(x, m2=m1, m1=m2, expect=False)

    def test_mask_2_fail_2(self):
        m1 = urandom(8)
        for x in self.get_x():
            self.do_test(x, m2=m1, m1=None, expect=False)


class TestStrArt(AbstractArt, unittest.TestCase):
    def get_x(self):
        return ['16546', '12315', 'asjh', 'test string']


class TestIntArt(AbstractArt, unittest.TestCase):
    def get_x(self):
        return [54946, 32874, -459983, 23983, 8374]


class TestFloatArt(AbstractArt, unittest.TestCase):
    def get_x(self):
        return [
            54946.124,
            0.32874,
            -45.9983,
            0.000000002,
            8374 * 10 ** 9 + 0.1,
        ]


class TestListArt(AbstractArt, unittest.TestCase):
    def get_x(self):
        return [
            [1, [2, []], 3],
            [],
            [0] * 138,
        ]


class TestDictArt(AbstractArt, unittest.TestCase):
    def get_x(self):
        return [
            {},
            {1: 2, '2': 123},
            {'a': {132: {'1241': [{1.1: False, 2.8: True}]}}},
        ]
