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


def _normalize_objects(objects):
    normalized_objects = []
    for object in objects:
        try:
            if isinstance(object, dict):
                normalized_objects.append(object)
            else:
                normalized_objects.append(json.loads(object))
        # TODO: Should be a JsonDecoderError
        except Exception:
            if '=' in object:
                normalized_objects.append(_split(object))
            else:
                normalized_objects.append({'_bad_object': object})
    return normalized_objects


class Pen(object):
    def __init__(self,
                 name=None,
                 hostname=None,
                 level='info',
                 pretty=None,
                 jsonify=False):
        self.obj = self._get_base(name, hostname)
        self.pretty = pretty
        self.jsonify = jsonify

        self.logger = self._logger(name, level)

    @staticmethod
    def _get_base(name, hostname):
        return {
            'name': name or __name__,
            'hostname': hostname or socket.gethostname(),
            'pid': os.getpid(),
        }

    def _logger(self, name, level):
        if level not in LEVEL_CONVERSION.keys():
            raise PenError('Level must be one of {0}'.format(
                LEVEL_CONVERSION.keys()))

        handler = logging.StreamHandler(sys.stdout)
        if self.jsonify:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(LEVEL_CONVERSION[level])
        return logger

    def _format(self, obj):
        if self.jsonify:
            return json.dumps(obj, indent=4 if self.pretty else None)
        else:
            return obj

    @staticmethod
    def _get_timestamp():
        return datetime.datetime.now().isoformat()

    def _enrich(self, message, level, objects):
        # objects = list(objects)

        objects = _normalize_objects(objects)
        if self.jsonify:
            obj = self.obj.copy()
            obj.update(
                {
                    'message': message,
                    'level': level,
                    'timestamp': self._get_timestamp()
                }
            )
            for object in objects:
                obj.update(object)
            return obj
        else:
            for object in objects:
                if isinstance(object, dict):
                    object = json.dumps(object)
                message += ' ' + object
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


def debug(message, *objects):
    writer = Pen(level='debug')
    writer.debug(message, objects)


def info(message, *objects):
    writer = Pen(level='info')
    writer.info(message, *objects)


def warn(message, *objects):
    writer = Pen(level='warning')
    writer.warn(message, objects)


def warning(message, *objects):
    writer = Pen(level='warning')
    writer.warning(message, objects)


def error(message, *objects):
    writer = Pen(level='error')
    writer.error(message, objects)


def critical(message, *objects):
    writer = Pen(level='critical')
    writer.critical(message, objects)


class PenError(Exception):
    pass


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def main():
    pass


def _split(object):
    parts = object.split('=', 1)
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
    getattr(Pen(name=name, pretty=pretty, level=level, jsonify=jsonify),
            level.lower())(message, *objects)


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
    writer = Pen(name='TEST', jsonify=jsonify, pretty=pretty, level='info')
    # writer.info('My Message', {'x': 'y'}, {'a': 'b'}, 'p=1')
    writer.info('My Message', {'key': 'value'}, 'who=where')


# TODO: Allow to pass stream or list of streams
# TODO: Automatically identify exception objects and log them in a readable way
