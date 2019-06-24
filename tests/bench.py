from wryte import Wryte
import timeit
import statistics

w = Wryte(color=False, simple=False)
w.remove_handler('_console')

def benchmark(code, repeat=20, number=10000):
    print('Benchmarking: `{}`'.format(code))
    results = timeit.repeat(code, repeat=repeat, number=number, globals={'w': w})
    avg = sum(results) / len(results)
    p90 = sorted(results)[int(len(results)*0.9)]
    print('20 iterations: ')
    print('\n'.join(map(str, results)))
    print('avg: {}, P90: {}'.format(statistics.mean(results), p90))

benchmark('w.info("test message")')
benchmark('w.info("test message with context", {"key": "value"})')
benchmark('w.log("info", "test messge")')
# without handlers, simple message
# 648e0c2: ~260ms
# 764dc31: ~260ms
#
