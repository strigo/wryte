from wryte import Wryte

wryter = Wryte(level='INFO')

PATH = 'x'


def read_config(path):
    wryter.info('Loading application configuration...')
    wryter.debug('Reading Config {0}'.format(path))
    # ...
    raise Exception('Enabling Debug...')


config_file_read = False

wryter.info('Starting application...')

try:
    config = read_config(PATH)
    config_file_read = True
except Exception as ex:
    # Can also pass `set_level` to `critical`, not just to `error`.
    wryter.error('Failed to read config ({})'.format(
        ex), {'context': 'some_context'}, _set_level='debug')
    # do_something to reread the file, but this time with debug logging enabled.
    config = read_config(PATH)
    config_file_read = True
finally:
    if config_file_read:
        wryter.info('Success loading config...')
        wryter.set_level('info')
    else:
        raise RuntimeError('Completely failed to read config')
