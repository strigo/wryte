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


CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())


LEVEL_CONVERSION = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


class JsonFormatter(logging.Formatter):
    def __init__(self, pretty=False):
        self.pretty = pretty

    def format(self, record):
        return json.dumps(record.msg, indent=4 if self.pretty else None)


class ConsoleFormatter(logging.Formatter):
    def __init__(self, pretty=True):
        self.pretty = pretty

    def format(self, record):
        record = record.msg.copy()
        name = record.get('name')
        timestamp = record.get('timestamp')
        level = record.get('level')
        message = record.get('message')

        # We no longer need them as part of the dict.
        record.pop('name')
        record.pop('timestamp')
        record.pop('level')
        record.pop('message')

        # These aren't printed out in the console logger.
        record.pop('hostname')
        record.pop('pid')

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
                 jsonify=False):
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
            _formatter = ConsoleFormatter(self.pretty or True)
        else:
            _formatter = formatter
        handler.setFormatter(_formatter)
        handler.set_name(name)

        self.logger.setLevel(LEVEL_CONVERSION[level.lower()])
        self.logger.addHandler(handler)
        return name

    def list_handlers(self):
        return [handler.name for handler in self.logger.handlers]

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
            pid=os.getpid())

    @staticmethod
    def _logger(name):
        """Return a named logger instance.
        """
        logger = logging.getLogger(name)
        return logger

    @staticmethod
    def _split_kv(obj):
        """Return dict for key=value.
        """
        kv = obj.split('=', 1)
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
        objects = self._normalize_objects(objects)
        log = self.log_base.copy()
        for part in objects:
            log.update(part)
        log.update(dict(
            message=message,
            level=level.upper(),
            timestamp=self._get_timestamp()))
        return log

    def log(self, level, message, *objects):
        obj = self._enrich(message, 'debug', objects)
        self.logger.log(level, obj)

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
    '-p',
    '--pretty',
    is_flag=True,
    default=False)
@click.option(
    '-j',
    '--jsonify',
    is_flag=True,
    default=False)
@click.option(
    '-n',
    '--name',
    type=click.STRING,
    default=False)
def main(level, message, objects, pretty, jsonify, name):
    wryter = Wryte(name=name, pretty=pretty, level=level, jsonify=jsonify)
    getattr(wryter, level.lower())(message, *objects)
