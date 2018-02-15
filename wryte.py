# Copyright 2017 Nir Cohen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: Automatically identify exception objects and log them in a readable way


import os
import sys
import uuid
import json
import socket
import logging
import datetime

import click

try:
    import colorama
    from colorama import Fore, Style
    COLORAMA = True
except ImportError:
    COLORAMA = False


CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())


LEVEL_CONVERSION = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'event': logging.INFO
}


class JsonFormatter(logging.Formatter):
    def __init__(self, pretty=False):
        self.pretty = pretty

    def format(self, record):
        return json.dumps(record.msg, indent=4 if self.pretty else None)


class ConsoleFormatter(logging.Formatter):
    def __init__(self, pretty=True, color=True):
        self.pretty = pretty
        self.color = color

    @staticmethod
    def _get_level_color(level):
        mapping = {
            'debug': Fore.CYAN,
            'info': Fore.GREEN,
            'warning': Fore.YELLOW,
            'warn': Fore.YELLOW,
            'error': Fore.RED,
            'critical': Style.BRIGHT + Fore.RED,
            'event': Style.BRIGHT + Fore.GREEN,
        }
        return mapping.get(level.lower())

    def format(self, record):
        record = record.msg.copy()

        name = record.get('name')
        timestamp = record.get('timestamp')
        level = record.get('level') if record['type'] == 'log' else 'EVENT'
        message = record.get('message')

        # We no longer need them as part of the dict.
        p = ['name', 'timestamp', 'level', 'message', 'type', 'hostname', 'pid']
        for key in p:
            record.pop(key)

        if COLORAMA and self.color:
            level = str(self._get_level_color(level) + level + Style.RESET_ALL)
            timestamp = str(Fore.GREEN + timestamp + Style.RESET_ALL)
            name = str(Fore.MAGENTA + name + Style.RESET_ALL)

        msg = '{0} - {1} - {2} - {3}'.format(timestamp, name, level, message)
        if self.pretty:
            for key, value in record.items():
                msg += '\n  {0}={1}'.format(key, value)
        elif record:
            msg += '\n{0}'.format(json.dumps(record, indent=4))
        return msg


class Wryte(object):
    def __init__(self,
                 name=None,
                 hostname=None,
                 level='info',
                 pretty=None,
                 bare=False,
                 jsonify=False,
                 color=True):
        """Instantiate a logger instance.

        Either a JSON or a Console handler will be added to the logger
        unless `bare` is True. By default, a console handler will be added,
        unless `jsonify` is True.

        If `hostname` isn't provided, it will be retrieved via socket.
        """
        self.name = name or __name__
        self.pretty = pretty

        self.log_base = self._get_base(name, hostname)
        self.logger = self._logger(name)

        self.color = color
        if not bare:
            if not jsonify:
                self.add_default_console_handler(level)
            else:
                self.add_default_json_handler(level)

    def add_handler(self,
                    handler,
                    name=None,
                    formatter='json',
                    level='info'):
        """Add a handler to the logger instance.

        A handler can be any standard `logging` handler.
        Formatters are limited to `console` and json`.
        """
        if level.lower() not in LEVEL_CONVERSION.keys():
            raise WryteError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        name = name or str(uuid.uuid4())
        # TODO: Allow to ignore fields in json formatter
        # TODO: Allow to remove field printing in console formatter
        assert formatter in ('console', 'json')
        if formatter == 'json':
            _formatter = JsonFormatter(self.pretty or False)
        elif formatter == 'console':
            colorama.init(autoreset=True)
            pretty = True if self.pretty in (None, True) else False
            _formatter = ConsoleFormatter(pretty, self.color)
        else:
            _formatter = formatter
        handler.setFormatter(_formatter)
        handler.set_name(name)

        self.logger.setLevel(LEVEL_CONVERSION[level.lower()])
        self.logger.addHandler(handler)
        return name

    def list_handlers(self):
        return [handler.name for handler in self.logger.handlers]

    def set_level(self, level):
        if level.lower() not in LEVEL_CONVERSION.keys():
            raise WryteError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        self.logger.setLevel(level.upper())

    def remove_handler(self, name):
        for handler in self.logger.handlers:
            if handler.name == name:
                self.logger.removeHandler(handler)

    def add_default_json_handler(self, level):
        return self.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter='json',
            level=level)

    def add_default_console_handler(self, level):
        return self.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_console',
            formatter='console',
            level=level)

    @staticmethod
    def _get_base(name, hostname):
        """Generate base fields for each log message.
        """
        return dict(
            name=name,
            hostname=hostname or socket.gethostname(),
            pid=os.getpid(),
            type='log')

    @staticmethod
    def _logger(name):
        """Return a named logger instance.
        """
        logger = logging.getLogger(name)
        return logger

    @staticmethod
    def _split_kv(pair):
        """Return dict for key=value.
        """
        kv = pair.split('=', 1)
        return {kv[0]: kv[1]}

    def _normalize_objects(self, objects):
        """Return a normalized dictionary for a list of key value like objects.

        This supports parsing dicts, json strings and key=value pairs.

        e.g. for ['key1=value1', {'key2': 'value2'}, '{"key3":"value3"}']
        return dict {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        """
        normalized_objects = []
        for obj in objects:
            try:
                if isinstance(obj, dict):
                    normalized_objects.append(obj)
                else:
                    normalized_objects.append(json.loads(obj))
            # TODO: Should be a JsonDecoderError
            except Exception:  # NOQA
                if '=' in obj:
                    normalized_objects.append(self._split_kv(obj))
                else:
                    normalized_objects.append({'_bad_object': obj})
        return normalized_objects

    @staticmethod
    def _get_timestamp():
        return datetime.datetime.now().isoformat()

    def _enrich(self, message, level, objects):
        """Returns a metadata enriched object which includes the level,
        message and keys provided in all objects.

        Example:

        Given 'MESSAGE', 'info', ['{"key1":"value1"}', 'key2=value2'],

        Return:
        {
            'timestamp': '2017-12-22T17:02:59.550920',
            'level': 'INFO',
            'message': 'MESSAGE',
            'key1': 'value1',
            'key2': 'value2',
            'name': 'my-logger-name',
            'hostname': 'my-host',
            'pid': 51223
        }
        """
        log = self.log_base.copy()

        objects = self._normalize_objects(objects)
        for part in objects:
            log.update(part)

        log.update(dict(
            message=message,
            level=level.upper(),
            timestamp=self._get_timestamp()))
        return log

    def bind(self, *objects):
        objects = self._normalize_objects(objects)
        for part in objects:
            self.log_base.update(part)

    def unbind(self, *keys):
        for key in keys:
            self.log_base.pop(key)

    def event(self, message, *objects):
        cid = str(uuid.uuid4())
        objects = objects + ({'type': 'event', 'cid': cid},)
        obj = self._enrich(message, 'info', objects)
        self.logger.info(obj)
        return {'cid': cid}

    def log(self, level, message, *objects):
        obj = self._enrich(message, level, objects)
        self.logger.log(LEVEL_CONVERSION[level], obj)

    def debug(self, message, *objects):
        obj = self._enrich(message, 'debug', objects)
        self.logger.debug(obj)

    def info(self, message, *objects):
        obj = self._enrich(message, 'info', objects)
        self.logger.info(obj)

    def warn(self, message, *objects):
        obj = self._enrich(message, 'warning', objects)
        self.logger.warning(obj)

    def warning(self, message, *objects):
        obj = self._enrich(message, 'warning', objects)
        self.logger.warning(obj)

    def error(self, message, *objects):
        obj = self._enrich(message, 'error', objects)
        self.logger.error(obj)

    def critical(self, message, *objects):
        obj = self._enrich(message, 'critical', objects)
        self.logger.critical(obj)


class WryteError(Exception):
    pass


@click.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument('LEVEL')
@click.argument('MESSAGE')
@click.argument('OBJECTS', nargs=-1)
@click.option(
    '--pretty/--ugly',
    is_flag=True,
    default=True)
@click.option(
    '-j',
    '--json',
    'jsonify',
    is_flag=True,
    default=False)
@click.option(
    '-n',
    '--name',
    type=click.STRING,
    default='Wryte')
@click.option(
    '--no-color',
    is_flag=True,
    default=False)
def main(level, message, objects, pretty, jsonify, name, no_color):
    wryter = Wryte(name=name, pretty=pretty, level=level,
                   jsonify=jsonify, color=not no_color)
    getattr(wryter, level.lower())(message, *objects)


if __name__ == "__main__":
    wryter = Wryte(name='Wryte', level='debug')
    wryter.info('Logging an error level message:')
    wryter.log('error', 'w00t')

    wryter.info('Logging an event:')
    wryter.event('w00t')

    wryter.info('Binding more dicts to the logger:')
    wryter.bind({'bound1': 'value1'}, 'bound2=value2')
    wryter.info('bind_test')

    wryter.info('Unbinding keys:')
    wryter.unbind('bound1')
    wryter.critical('unbind_test')
