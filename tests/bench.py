from datetime import datetime

import numpy

from wryte import Wryte


def _test_simple_message(count):
    w = Wryte(color=False, simple=True)
    w.remove_handler('_console')
    timing = []

    for _ in range(5):
        now = datetime.now()

        for _ in range(count):
            w.info('My Message')

        timing.append((datetime.now() - now).total_seconds() * 1000.0)

    return numpy.average(timing[1:])


for _ in range(15):
    result = _test_simple_message(10000)
    print(result)

# without handlers, simple message
# 648e0c2: ~260ms
# 764dc31: ~260ms
#
