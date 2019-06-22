from datetime import datetime
import pytest
import timeit

import wryte
from wryte import Wryte

def average(numbers):
    return sum(numbers) / float(len(numbers))


class TestPerf(object):
    def _test_simple_message(self):
        w = Wryte(color=False, simple=True)
        results = timeit.repeat('w.info(\'My Message\')', repeat=5, number=1000, globals={'w': w})
        # This is just a benchmark. This should NEVER take this long.
        assert average(results) < 1

    def test_simple_context(self):
        w = Wryte(color=False)


        results = timeit.repeat("w.info('My Message', {'key': 'value'})", repeat=5, number=1000, globals={'w': w})


        # This is just a benchmark. This should NEVER take this long.
        assert average(results) < 1
