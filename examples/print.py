from wryte import Wryte

wryter = Wryte(name='Wryte', level='info')
wryter.info('Logging an error level message:')
wryter.log('error', 'w00t')

wryter.info('Logging an event:', w00t='d')
wryter.event('w00t')

wryter.info('Binding more dicts to the logger:')
wryter.bind({'bound1': 'value1'}, bound2='value2')
wryter.info('bind_test')

wryter.info('Unbinding keys:')
wryter.unbind('bound1')
wryter.critical('unbind_test')

wryter.error('w00t', _set_level='debug')

wryter.debug('test-kwargs', key1='value')
wryter.error('message', _set_level='info', x='y', a='b')
wryter.debug('test-kwargs', key1='value')
