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
    # def __init__(self):
    #     super(JsonFormatter, self).__init__()

    def format(self, record):
        data = record.msg
        print(type(data))
        return json.dumps(data)


class Wryte(object):
    def __init__(self,
                 name=None,
                 hostname=None,
                 level='info',
                 pretty=None,
                 jsonify=False):
        if jsonify:
            self.obj = self._get_base(name, hostname)
        else:
            self.obj = {}
        self.pretty = pretty
        self.jsonify = jsonify

        self.logger = self._logger(name, level)

    @staticmethod
    def _get_base(name, hostname):
        return dict(
            name=name or __name__,
            hostname=hostname or socket.gethostname(),
            pid=os.getpid())

    def add_handler(self, handler, formatter='console', level='info'):
        if level not in LEVEL_CONVERSION.keys():
            raise WryteError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        assert formatter in ('console', 'json')
        if formatter == 'json':
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.setLevel(LEVEL_CONVERSION[level])
        self.logger.addHandler(handler)

    def _logger(self, name, level):
        if level not in LEVEL_CONVERSION.keys():
            raise WryteError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        logger = logging.getLogger(name)
        if self.jsonify:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(LEVEL_CONVERSION[level])

        return logger

    def _format(self, obj):
        if self.jsonify:
            return json.dumps(obj, indent=4 if self.pretty else None)
        else:
            return obj

    @staticmethod
    def _normalize_objects(objects):
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
                    normalized_objects.append(_split(obj))
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
        if self.jsonify:
            obj.update(dict(
                message=message,
                level=level,
                timestamp=self._get_timestamp()))
            return obj
        else:
            for k, v in obj.items():
                message += '\n  {0}={1}'.format(k, v)
            return message

    def debug(self, message, *objects):
        obj = self._enrich(message, 'debug', objects)
        self.logger.debug(self._format(obj))

    def info(self, message, *objects):
        obj = self._enrich(message, 'info', objects)
        self.logger.info(self._format(obj))

    def warn(self, message, *objects):
        obj = self._enrich(message, 'warning', objects)
        self.logger.warning(self._format(obj))

    def warning(self, message, *objects):
        obj = self._enrich(message, 'warning', objects)
        self.logger.warning(self._format(obj))

    def error(self, message, *objects):
        obj = self._enrich(message, 'error', objects)
        self.logger.error(self._format(obj))

    def critical(self, message, *objects):
        obj = self._enrich(message, 'critical', objects)
        self.logger.critical(self._format(obj))


class WryteError(Exception):
    pass


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def main():
    pass


def _split(obj):
    parts = obj.split('=', 1)
    kv = {parts[0]: parts[1]}
    return kv


@main.command()
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
def write(level, message, objects, pretty, jsonify, name):
    writer = Wryte(name=name, pretty=pretty, level=level, jsonify=jsonify)
    writer.add_handler(logging.StreamHandler(sys.stdout), 'json', 'debug')
    getattr(writer, level.lower())(message, *objects)


@main.command()
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
def test(pretty, jsonify):
    writer = Wryte(name='TEST', jsonify=jsonify, pretty=pretty, level='info')
    writer.add_handler(logging.FileHandler('x.log'), 'json', 'debug')
    # writer.info('My Message', {'x': 'y'}, {'a': 'b'}, 'p=1')
    writer.info('My Message', {'key': 'value'}, 'who=where')

# TODO: Automatically identify exception objects and log them in a readable way
