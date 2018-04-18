from datetime import datetime

import numpy
import pytest

import wryte
from wryte import Wryte


class TestPerf(object):
    # 1 message takes ~0.067ms
    def _test_simple_message(self):
        w = Wryte(color=False, simple=True)

        timing = []

        for _ in range(5):
            now = datetime.now()

            for _ in range(10):
                w.info('My Message')

            timing.append((datetime.now() - now).total_seconds() * 1000.0)

        # This is just a benchmark. This should NEVER take this long.
        assert numpy.average(timing[1:]) < 10

    def test_simple_context(self):
        w = Wryte(color=False)

        timing = []

        for _ in range(5):
            now = datetime.now()

            for _ in range(10):
                w.info('My Message', {'key': 'value'})

            timing.append((datetime.now() - now).total_seconds() * 1000.0)

        # This is just a benchmark. This should NEVER take this long.
        assert numpy.average(timing[1:]) < 2
