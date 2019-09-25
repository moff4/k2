import asyncio
import unittest

from k2.stats import stats

LOOP = asyncio.get_event_loop()


class TestStats(unittest.TestCase):
    def test_single(self):
        key = 'test-single'
        stats.new(key, stats.STATS_TYPE_SINGLE)
        LOOP.run_until_complete(stats.add(key, 'TestVal_1'))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': 'TestVal_1'},
            'type': stats.STATS_TYPE_SINGLE,
            'description': None,
        })
        LOOP.run_until_complete(stats.add(key, 'TestVal_2'))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': 'TestVal_2'},
            'type': stats.STATS_TYPE_SINGLE,
            'description': None,
        })

    def test_counter(self):
        key = 'test-counter'
        stats.new(key, stats.STATS_TYPE_COUNTER)
        LOOP.run_until_complete(stats.add(key))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': 1, 'default': 0},
            'type': stats.STATS_TYPE_COUNTER,
            'description': None,
        })
        LOOP.run_until_complete(stats.add(key, 15))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': 16, 'default': 0},
            'type': stats.STATS_TYPE_COUNTER,
            'description': None,
        })

    def test_average(self):
        key = 'test-average'
        stats.new(key, stats.STATS_TYPE_AVERAGE)
        LOOP.run_until_complete(stats.add(key, 150))
        self.assertEqual(stats.export_one(key), {
            'data': {'count': 1, 'data': 150, 'limit': 500},
            'type': stats.STATS_TYPE_AVERAGE,
            'description': None,
        })
        LOOP.run_until_complete(stats.add(key, 13))
        self.assertEqual(stats.export_one(key), {
            'data': {'count': 2, 'data': (150 + 13) / 2, 'limit': 500},
            'type': stats.STATS_TYPE_AVERAGE,
            'description': None,
        })
        LOOP.run_until_complete(stats.add(key, 99))
        self.assertEqual(stats.export_one(key), {
            'data': {'count': 3, 'data': (150 + 13 + 99) / 3, 'limit': 500},
            'type': stats.STATS_TYPE_AVERAGE,
            'description': None,
        })

    def test_event_counter(self):
        key = 'test-event-counter'
        stats.new(key, stats.STATS_TYPE_EVENTCOUNTER)
        LOOP.run_until_complete(stats.add(key, 'event-1'))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': {'event-1': 1}},
            'type': stats.STATS_TYPE_EVENTCOUNTER,
            'description': None,
        })
        LOOP.run_until_complete(stats.add(key, 'event-1'))
        LOOP.run_until_complete(stats.add(key, 'event-2'))
        LOOP.run_until_complete(stats.add(key, 'event-1'))
        LOOP.run_until_complete(stats.add(key, 'event-2'))
        LOOP.run_until_complete(stats.add(key, 'event-2'))
        LOOP.run_until_complete(stats.add(key, 'event-1'))
        self.assertEqual(stats.export_one(key), {
            'data': {'data': {'event-1': 4, 'event-2': 3}},
            'type': stats.STATS_TYPE_EVENTCOUNTER,
            'description': None,
        })
