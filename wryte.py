# pylint: disable=missing-docstring

# Copyright 2017-2018 Nir Cohen
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
import uuid
import json
import socket
import logging
import logging.handlers
from datetime import datetime

# pytype: disable=import-error
try:
    # Python 2
    import urllib2 as urllib
except ImportError:
    # Python 3
    import urllib.request as urllib

try:
    import colorama
    from colorama import Fore, Style

    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

try:
    import click  # pytype: disable=pyi-error

    CLI_ENABLED = True
except ImportError:
    CLI_ENABLED = False
# pytype: enable=import-error


LEVEL_CONVERSION = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'event': logging.INFO,
}


class JsonFormatter(logging.Formatter):
    def __init__(self, pretty=False):
        self.pretty = pretty

    def format(self, record):
        return json.dumps(record.msg, indent=4 if self.pretty else None)


class ConsoleFormatter(logging.Formatter):
    def __init__(self, pretty=True, color=True, simple=False):
        self.pretty = pretty
        self.color = color

        _simple = os.getenv('WRYTE_SIMPLE_CONSOLE')

        if _simple is not None:
            self.simple = _simple == "true"
        else:
            self.simple = simple

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
        """Formats the message to be human readable

        This formatter receives a dictionary as `msg`. It then removes
        irrelevant fields and declare generates a string that looks like so:

        2018-02-01T15:01:08 - MyLogger - INFO - My interesting message
            key1=value1
            key2=value2

         * If `simple` is True, only `message` will be printed inline.
         * If `pretty` is True, kv's will be printed as json instead of k=v
         * If `color` is True, fields will be printed in color.

        Note that coloring has a significant performance cost so you should
        not use color if you're not logging in a CLI client
        (but rather to journald or whatever).

        Performance is also reduced by the amount of fields you have in your
        context (context i.e. k=v).
        """
        record = record.msg.copy()

        # Not popping and deleting later as pop is marginally less performant
        name = record['name']
        timestamp = record['timestamp']
        level = record['level'] if record['type'] == 'log' else 'EVENT'
        message = record['message']
        # We no longer need them as part of the dict.
        drop_keys = ('level', 'type', 'hostname', 'pid', 'name', 'message', 'timestamp')
        for key in drop_keys:
            del record[key]

        if COLOR_ENABLED and self.color and not self.simple:
            level = str(self._get_level_color(level) + level + Style.RESET_ALL)
            timestamp = str(Fore.GREEN + timestamp + Style.RESET_ALL)
            name = str(Fore.MAGENTA + name + Style.RESET_ALL)

        msg = message if self.simple else ' - '.join((timestamp, name, level, message))

        if self.pretty:
            # https://codereview.stackexchange.com/questions/7953/flattening-a-dictionary-into-a-string
            msg += ''.join("\n  %s=%s" % item for item in record.items())
        elif record:
            msg += '\n{}'.format(json.dumps(record, indent=4))

        return msg


class Wryte:
    def __init__(
        self,
        name=None,
        hostname=None,
        level='info',
        pretty=None,
        bare=False,
        jsonify=False,
        color=True,
        simple=False,
        enable_ec2=False,
    ):
        """Instantiate a logger instance.

        Either a JSON or a Console handler will be added to the logger
        unless `bare` is True. By default, a console handler will be added,
        unless `jsonify` is True.

        If `hostname` isn't provided, it will be retrieved via socket.

        See `ConsoleFormatter` for information on `color`, `pretty` and
        `simple`.

        `self.logger` exposes the stdlib's logging API directly so that
        the logger isn't bound only by what Wryte provides.
        """
        self.logger_name = name or __name__

        self.pretty = pretty
        self.color = color
        self.simple = simple

        self.logger = self._logger(self.logger_name)
        self._log = self._get_base(self.logger_name, hostname, enable_ec2)

        if not bare:
            self._configure_handlers(level, jsonify)

    @staticmethod
    def _logger(name):
        """Return a named logger instance."""
        logger = logging.getLogger(name)
        return logger

    def _get_base(self, name, hostname, enable_ec2=False):
        """Generate base fields for each log message.

        This is evaluated once when the logger's instance is instantiated.
        It is then later copied by each log message.
        """

        def fetch_ec2(attribute):
            try:
                return urllib.urlopen('http://169.254.169.254/latest/meta-data/{}'.format(attribute)).read().decode()
            # Yuch. But shouldn't take a risk that any exception will raise
            except Exception:  # pylint: disable=broad-except
                return None

        base = {
            'name': name,
            'hostname': hostname or socket.gethostname(),
            'pid': os.getpid(),
            'type': 'log',
        }

        if self._env('EC2_ENABLED') or enable_ec2:
            # To test that ec2 data is actually attainable
            instance_id = fetch_ec2('instance-id')
            if instance_id:
                base['ec2_instance_id'] = instance_id
                base['ec2_instance_type'] = fetch_ec2('instance-type')
                base['ec2_region'] = fetch_ec2('placement/availability-zone')
                base['ec2_ipv4'] = fetch_ec2('local-ipv4')
            else:
                self.logger.error(
                    'WRYTE EC2 env var set but EC2 metadata endpoint is '
                    'unavailable or the data could not be retrieved.'
                )

        return base

    @staticmethod
    def _get_timestamp():
        # `now()` needs to compensate for timezones, and so it takes much
        # more time to evaluate. `udatetime` doesn't help here and actually
        # takes more time both on Python2 and Python3.
        # This is by no means a reason to use utcnow,
        # but since we should standardize the timestamp, it makes sense to do
        # so anyway.
        return datetime.utcnow().isoformat()

    @staticmethod
    def _normalize_objects(objects):
        """Return a normalized dictionary for a list of key value like objects.

        This supports parsing dicts, json strings and key=value pairs.

        e.g. for ['key1=value1', {'key2': 'value2'}, '{"key3":"value3"}']
        return dict {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

        A `bad_object_uuid` field will be added to the context if an object
        doesn't fit the supported formats.
        """
        consolidated = {}

        for obj in objects:
            # We if here instead of try-excepting since it's not obvious
            # what the distribution between dict and json will be and if
            # costs much less when the distribution is flat.
            if isinstance(obj, dict):
                consolidated.update(obj)
            else:
                try:
                    consolidated.update(json.loads(obj))
                except Exception:  # pylint: disable=broad-except
                    consolidated['_bad_object_{}'.format(str(uuid.uuid4()))] = obj
        return consolidated

    def _enrich(self, message, level, objects, kwargs=None):
        """Return a metadata enriched object which includes the level,
        message and keys provided in all objects.

        Example:

        Given 'MESSAGE', 'info', ['{"key1":"value1"}', 'key2=value2'] k=v,

        Return:
        {
            'timestamp': '2017-12-22T17:02:59.550920',
            'level': 'INFO',
            'message': 'MESSAGE',
            'key1': 'value1',
            'key2': 'value2',
            'k': 'v',
            'name': 'my-logger-name',
            'hostname': 'my-host',
            'pid': 51223
        }
        """
        log = self._log.copy()

        # Normalizes and adds dictionary-like context.
        log.update(self._normalize_objects(objects))

        # Adds k=v like context
        if kwargs:
            log.update(kwargs)

        # Appends default fields.
        log['message'] = message
        log['level'] = level.upper()
        log['timestamp'] = self._get_timestamp()

        return log

    def _env(self, variable, default=None):
        """Return the value of an environment variable if it is set.

        This is done by first looking at `WRYTE_LOGGER_NAME_VARIABLE`
        and then looking at the more general `WRYTE_VARIABLE`.

        For example, `WRYTE_MY_LOGGER_HANDLERS_LOGZIO_TOKEN` will return
        the content of `WRYTE_MY_LOGGER_HANDLERS_LOGZIO_TOKEN` if it is
        set and will only apply to the `MY_LOGGER` logger.

        Setting the variable `WRYTE_HANDLERS_LOGZIO_TOKEN` means
        that it applies to all loggers.
        """
        logger_env = os.getenv('WRYTE_{}_{}'.format(self.logger_name.upper(), variable))
        global_env = os.getenv('WRYTE_{}'.format(variable))
        return logger_env or global_env or default

    def _configure_handlers(self, level, jsonify=False):
        """Configure handlers for the logger's instance.

        This is done on instantiation.
        """
        if not self._env('CONSOLE_DISABLED'):
            if self._env('CONSOLE_JSONIFY', jsonify):
                self.add_default_json_handler(level)
            else:
                self.add_default_console_handler(level)

        if self._env('HANDLERS_FILE_PATH'):
            self.add_file_handler()

    def _assert_level(self, level):
        levels = LEVEL_CONVERSION.keys()

        if level.lower() not in levels:
            self.logger.exception('Level must be one of %s', levels)
            return False
        return True

    def add_handler(self, handler, name=None, formatter='json', level='info'):
        """Add a handler to the logger instance and return its name.

        A `handler` can be any standard `logging` handler.
        `formatter` can be one of `console`, `json` or a formatter instance.

        Choosing `console`/`json` will use the default console/json handlers.
        `name` is the handler's name (not the logger's name).
        """
        name = name or str(uuid.uuid4())

        if self._assert_level(level):
            self.logger.setLevel(LEVEL_CONVERSION[level.lower()])
        else:
            return ''

        if formatter == 'json':
            _formatter = JsonFormatter(self.pretty or False)
        elif formatter == 'console':
            if COLOR_ENABLED:
                colorama.init(autoreset=True)
            pretty = self.pretty in (None, True)
            _formatter = ConsoleFormatter(pretty, self.color, self.simple)
        else:
            _formatter = formatter

        handler.setFormatter(_formatter)
        try:
            handler.set_name(name)  # pytype: disable=attribute-error
        except AttributeError:
            handler.name = name

        self.logger.addHandler(handler)

        return name

    def list_handlers(self):
        """Return a list of all handlers attached to a logger"""
        return [handler.name for handler in self.logger.handlers]

    def remove_handler(self, name):
        """Remove a handler by its name (set in `add_handler`)"""
        for handler in self.logger.handlers:
            if handler.name == name:
                self.logger.removeHandler(handler)

    def add_default_json_handler(self, level='debug'):
        return self.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter='json',
            level=self._env('CONSOLE_LEVEL', level),
        )

    def add_default_console_handler(self, level='debug'):
        name = '_console'
        level = self._env('CONSOLE_LEVEL', default=level)
        formatter = 'console'
        handler = logging.StreamHandler(sys.stdout)

        return self.add_handler(handler=handler, name=name, formatter=formatter, level=level)

    def add_file_handler(self):
        if not self._env('HANDLERS_FILE_PATH'):
            self.logger.warning('File handler file path not set')
            return

        name = self._env('HANDLERS_FILE_NAME', default='file')
        level = self._env('HANDLERS_FILE_LEVEL', default='info')
        formatter = self._env('HANDLERS_FILE_FORMATTER', default='json')

        if self._env('HANDLERS_FILE_ROTATE'):
            try:
                max_bytes = int(self._env('HANDLERS_FILE_MAX_BYTES', default=13107200))
                backup_count = int(self._env('HANDLERS_FILE_BACKUP_COUNT', default=7))
            except ValueError:
                self.logger.exception('MAX_BYTES and BACKUP_COUNT must be integers')
                return

            handler = logging.handlers.RotatingFileHandler(
                self._env('HANDLERS_FILE_PATH'), maxBytes=max_bytes, backupCount=backup_count
            )
        elif os.name == 'nt':
            handler = logging.FileHandler(self._env('HANDLERS_FILE_PATH'))
        else:
            handler = logging.handlers.WatchedFileHandler(self._env('HANDLERS_FILE_PATH'))

        self.add_handler(handler=handler, name=name, formatter=formatter, level=level)

    def set_level(self, level):
        """Set the current logger instance's level."""
        if not self._assert_level(level):
            return

        self.logger.setLevel(level.upper())

    def bind(self, *objects, **kwargs):
        """Bind context to the logger's instance.

        After binding, each log entry will contain the bound fields.
        """
        self._log.update(self._normalize_objects(objects))

        if kwargs:
            self._log.update(kwargs)

    def unbind(self, *keys):
        """Unbind previously bound context."""
        for key in keys:
            # Perf-wise, we should try-except here since we expect
            # that 99% of the time the keys will exist so it will be faster.
            # Thing is, that unbinding shouldn't happen thousands of
            # times a second, so we'll go for readability here.
            self._log.pop(key)

    def event(self, message, *objects, **kwargs):
        """Log an event and return a cid for it.

        Once an event is fired, a `cid` is generated for it unless
        explicitly passed in kwargs. Additionally, the `type` of the
        log will be `event`, instead of log, like in other cases.
        """
        cid = kwargs.get('cid', str(uuid.uuid4()))
        objects = objects + ({'type': 'event', 'cid': cid},)
        obj = self._enrich(message, 'info', objects, kwargs)
        self.logger.info(obj)
        return cid

    def log(self, level, message, *objects, **kwargs):
        """Just log.

        This is meant to be used programatically when you
        don't know what the level will be in advance.

        This is provided so that you don't have to use
        `getattr(logger, level)()` and instead just use
        logger.log(level, message, ...)

        Note that This is less performant than other logging methods
        (e.g. info, debug) as level conversion takes place since the user
        can practically pass weird logging levels.
        """
        obj = self._enrich(message, level, objects, kwargs)
        if '_set_level' in kwargs:
            self.set_level(kwargs['_set_level'])

        if not self._assert_level(level):
            return
        self.logger.log(LEVEL_CONVERSION[level], obj)

    # Ideally, we'd use `self.log` for all of these, but since
    # level conversion would affect performance, it's better to now to
    # until figuring something out.
    def debug(self, message, *objects, **kwargs):
        obj = self._enrich(message, 'debug', objects, kwargs)
        self.logger.debug(obj)

    def info(self, message, *objects, **kwargs):
        obj = self._enrich(message, 'info', objects, kwargs)
        self.logger.info(obj)

    def warn(self, message, *objects, **kwargs):
        obj = self._enrich(message, 'warning', objects, kwargs)
        self.logger.warning(obj)

    def warning(self, message, *objects, **kwargs):
        obj = self._enrich(message, 'warning', objects, kwargs)
        self.logger.warning(obj)

    def error(self, message, *objects, **kwargs):
        if '_set_level' in kwargs:
            self.set_level(kwargs['_set_level'])
        obj = self._enrich(message, 'error', objects, kwargs)
        self.logger.error(obj)

    def critical(self, message, *objects, **kwargs):
        if '_set_level' in kwargs:
            self.set_level(kwargs['_set_level'])
        obj = self._enrich(message, 'critical', objects, kwargs)
        self.logger.critical(obj)


class WryteError(Exception):
    pass


def _split_kv(pair):
    """Return dict for key=value."""
    key_value = pair.split('=', 1)
    return {key_value[0]: key_value[1]}


if CLI_ENABLED:
    CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], token_normalize_func=lambda param: param.lower())

    @click.command(context_settings=CLICK_CONTEXT_SETTINGS)
    @click.argument('LEVEL')
    @click.argument('MESSAGE')
    @click.argument('OBJECTS', nargs=-1)
    @click.option(
        '--pretty/--ugly', is_flag=True, default=True, help='Output JSON instead of key=value pairs for console logger'
    )
    @click.option(
        '-j',
        '--json',
        'jsonify',
        is_flag=True,
        default=False,
        help='Use the JSON logger formatter instead of the console one',
    )
    @click.option('-n', '--name', type=click.STRING, default='Wryte', help="Change the default logger's name")
    @click.option('--no-color', is_flag=True, default=False, help='Disable coloring in console formatter')
    @click.option('--simple', is_flag=True, default=False, help='Log only message to the console')
    def main(level, message, objects, pretty, jsonify, name, no_color, simple):
        wryter = Wryte(name=name, pretty=pretty, level=level, jsonify=jsonify, color=not no_color, simple=simple)

        objcts = []

        # Allows to pass `k=v` pairs.
        for obj in objects:
            try:
                json.loads(obj)
                objcts.append(obj)
            except Exception:  # pylint: disable=broad-except
                if '=' in obj:
                    objcts.append(_split_kv(obj))

        getattr(wryter, level.lower())(message, *objcts)


else:

    def main():
        sys.exit(
            "To use Wryte's CLI you must first install certain dependencies. "
            "Please run `pip install wryte[cli]` to enable the CLI."
        )
