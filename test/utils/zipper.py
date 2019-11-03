import os
import unittest

from k2.utils.zipper import (
    compress,
    arch_info,
    decompress,
)


class TestZipper(unittest.TestCase):

    def do_test(self, x, y, opt1=None, opt2=None, max_arch_size=175 * 2 ** 20, parts_num=None, expect=False):
        opt1 = opt1 or {}
        opt2 = opt2 or {}
        try:
            compressed = compress(x, opt1, max_arch_size)
            if parts_num:
                self.assertEqual(parts_num, len(compressed))
            z = decompress(compressed, opt2)
            self.assertEqual(z, y)
        except (RuntimeError, ValueError, TypeError, OverflowError):
            self.assertTrue(expect)

    def test_simple(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
            ],
            parts_num=1,
        )

    def test_simple_2(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            parts_num=1,
        )

    def test_simple_mask(self):
        mask = os.urandom(8)
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
            ],
            opt1={'art_mask': mask},
            opt2={'art_mask': mask},
            parts_num=1,
        )

    def test_simple_2_mask(self):
        mask = os.urandom(8)
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            opt1={'art_mask': mask},
            opt2={'art_mask': mask},
            parts_num=1,
        )

    def test_simple_fail(self):
        mask1 = os.urandom(8)
        mask2 = os.urandom(8)
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
            ],
            opt1={'art_mask': mask1},
            opt2={'art_mask': mask2},
            expect=True,
            parts_num=1,
        )

    def test_simple_2_fail(self):
        mask1 = os.urandom(8)
        mask2 = os.urandom(8)
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            y=[
                (b'./f1.txt', b'0123456789'),
                (b'./1/f2.txt', b'9876543210'),
            ],
            opt1={'art_mask': mask1},
            opt2={'art_mask': mask2},
            expect=True,
            parts_num=1,
        )

    def test_big(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
            ],
            y=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
            ],
            parts_num=1,
        )

    def test_big_2(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
                (b'./1/f2.txt', b'9876543210' * 2 ** 10),
            ],
            y=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
                (b'./1/f2.txt', b'9876543210' * 2 ** 10),
            ],
            parts_num=1,
        )

    def test_partied(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
            ],
            y=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
            ],
            max_arch_size=2 ** 13,
            parts_num=2,
        )

    def test_partied_2(self):
        self.do_test(
            x=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
                (b'./1/f2.txt', b'9876543210' * 2 ** 10),
            ],
            y=[
                (b'./f1.txt', b'0123456789' * 2 ** 10),
                (b'./1/f2.txt', b'9876543210' * 2 ** 10),
            ],
            max_arch_size=2 ** 14,
            parts_num=2,
        )

    def test_arch_info(self):
        opt = {'art_mask': os.urandom(9)}
        fn1 = b'./f1.txt'
        fn2 = b'./2/f2.txt'
        arch = compress(
            files=[
                (fn1, b'0123456789' * 2 ** 10),
                (fn2, b'QwErTy' * 2 ** 10),
            ],
            options=opt,
        )
        self.assertEqual(len(arch), 1)
        info = arch_info(arch, opt)
        self.assertEqual(len(info), 2)
        self.assertEqual(info, [('0', fn1), ('1', fn2)])
