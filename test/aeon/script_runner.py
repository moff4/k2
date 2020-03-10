
from unittest import TestCase
import asyncio

from k2.logger import new_channel
from k2.aeon import ScriptRunner


LOOP = asyncio.get_event_loop()
LOGGER = new_channel('test')


class TestScriptRunner(TestCase):

    def do_test(self, corotine, error=False, **kwargs):
        try:
            return LOOP.run_until_complete(corotine)
        except Exception:
            self.assertTrue(error)

    def test_empty(self):
        sr = ScriptRunner(text='', args={}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), '')

    def test_simple_none(self):
        sr = ScriptRunner(text='123 smth 1231', args={}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), '123 smth 1231')

    def test_simple_some(self):
        sr = ScriptRunner(text='/*# "123" #*/', args={}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), '123')

    def test_simple_some_more(self):
        sr = ScriptRunner(text='x/*# "123" #*/y', args={}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), 'x123y')

    def test_vars_1(self):
        sr = ScriptRunner(text='/*# str(123 + x) #*/', args={'x': 213}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), str(123 + 213))

    def test_vars_2(self):
        sr = ScriptRunner(text='/*# "*".join([*x, *y]) #*/', args={'x': ['213'], 'y': ('a', 'b', 'c')}, logger=LOGGER)
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), '213*a*b*c')

    def test_hard(self):
        sr = ScriptRunner(
            text='''/*#@
result = "*".join([*x, *y])
for i in range(3):
    result += str(i)
result += '-123-'
            @#*/''',
            args={'x': ['213'], 'y': ('a', 'b', 'c')},
            logger=LOGGER,
        )
        self.assertTrue(self.do_test(sr.run()))
        self.assertEqual(sr.export(), '213*a*b*c012-123-')
