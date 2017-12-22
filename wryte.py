# Copyright 2015,2016 Nir Cohen
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
        else:
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
        self.obj = self._get_base(name, hostname)
        self.pretty = pretty

        self.logger = self._logger(name)
        if not bare:
            if not jsonify:
                self.add_handler(
                    handler=logging.StreamHandler(sys.stdout),
                    formatter='console',
                    level=level)
            else:
                self.add_handler(
                    handler=logging.StreamHandler(sys.stdout),
                    formatter='json',
                    level=level)
        # TODO: If `bare`, deal with when no handler is supplied.

    @staticmethod
    def _get_base(name, hostname):
        return dict(
            name=name or __name__,
            hostname=hostname or socket.gethostname(),
            pid=os.getpid())

    def add_handler(self, handler, formatter='console', level='info'):
        if level.lower() not in LEVEL_CONVERSION.keys():
            raise WryteError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        # TODO: Allow to ignore fields in json formatter
        # TODO: Allow to remove field printing in console formatter
        assert formatter in ('console', 'json')
        if formatter == 'json':
            formatter = JsonFormatter(self.pretty)
        else:
            formatter = ConsoleFormatter(self.pretty)
        handler.setFormatter(formatter)

        self.logger.setLevel(LEVEL_CONVERSION[level.lower()])
        self.logger.addHandler(handler)

    @staticmethod
    def _logger(name):
        logger = logging.getLogger(name)
        return logger

    @staticmethod
    def _split_kv(obj):
        parts = obj.split('=', 1)
        kv = {parts[0]: parts[1]}
        return kv

    def _normalize_objects(self, objects):
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
        objects = self._normalize_objects(objects)
        obj = self.obj.copy()
        for part in objects:
            obj.update(part)
        obj.update(dict(
            message=message,
            level=level.upper(),
            timestamp=self._get_timestamp()))
        return obj

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
    pen = Wryte(name=name, pretty=pretty, level=level, jsonify=jsonify)
    getattr(pen, level.lower())(message, *objects)
