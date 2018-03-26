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
import datetime

try:
    import colorama
    from colorama import Fore, Style
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

try:
    import click
    CLI_ENABLED = True
except ImportError:
    CLI_ENABLED = False

try:
    from logzio.handler import LogzioHandler
    LOGZIO_INSTALLED = True
except ImportError:
    LOGZIO_INSTALLED = False

try:
    from cmreslogging.handlers import CMRESHandler
    ELASTICSEARCH_INSTALLED = True
except ImportError:
    ELASTICSEARCH_INSTALLED = False


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
        # TODO: Allow to use ujson or radpijson via config
        return json.dumps(record.msg, indent=4 if self.pretty else None)


class ConsoleFormatter(logging.Formatter):
    def __init__(self, pretty=True, color=True, simple=False):
        self.pretty = pretty
        self.color = color

        _simple = os.getenv('WRYTE_SIMPLE_CONSOLE')

        if _simple is not None:
            self.simple = True if _simple == "true" else False
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
        # TODO: No need to copy here
        record = record.msg.copy()

        # TODO: pop instead so that we don't need to pop after
        name = record['name']
        timestamp = record['timestamp']
        level = record['level'] if record['type'] == 'log' else 'EVENT'
        message = record['message']

        # We no longer need them as part of the dict.
        p = ('name', 'timestamp', 'level', 'message',
             'type', 'hostname', 'pid')
        for key in p:
            # TODO: del instead of popping
            record.pop(key)

        if COLOR_ENABLED and self.color and not self.simple:
            # TODO: Use string formatting instead
            level = str(self._get_level_color(level) + level + Style.RESET_ALL)
            timestamp = str(Fore.GREEN + timestamp + Style.RESET_ALL)
            name = str(Fore.MAGENTA + name + Style.RESET_ALL)

        if self.simple:
            msg = message
        else:
            # TODO: Use ' - '.join((timestamp, name, level, message))
            msg = '{0} - {1} - {2} - {3}'.format(
                timestamp, name, level, message)

        if self.pretty:
            # TODO: Find an alternative to concat here
            # msg += ''.join("\n  %s=%s" % (k, v)
            #                for (k, v) in record.items())
            for key, value in record.items():
                msg += '\n  {0}={1}'.format(key, value)
        elif record:
            # TODO: Allow to use ujson or radpijson
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
                 color=True,
                 simple=False):
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

        self._log = self._get_base(self.logger_name, hostname)
        self.logger = self._logger(self.logger_name)

        if not bare:
            self._configure_handlers(level, jsonify)

    @staticmethod
    def _logger(name):
        """Return a named logger instance.
        """
        logger = logging.getLogger(name)
        return logger

    @staticmethod
    def _get_base(name, hostname):
        """Generate base fields for each log message.

        This is evaluated once when the logger's instance is instantiated.
        It is then later copied by each log message.
        """
        # TODO: Document that these are only generated once.
        return {
            'name': name,
            'hostname': hostname or socket.gethostname(),
            'pid': os.getpid(),
            'type': 'log'
        }

    @staticmethod
    def _get_timestamp():
        # TODO: Allow to use udatetime instead for faster evals
        return datetime.datetime.now().isoformat()

    def _normalize_objects(self, objects):
        """Return a normalized dictionary for a list of key value like objects.

        This supports parsing dicts, json strings and key=value pairs.

        e.g. for ['key1=value1', {'key2': 'value2'}, '{"key3":"value3"}']
        return dict {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

        A `bad_object_uuid` field will be added to the context if an object
        doesn't fit the supported formats.
        """
        # TODO: Generate a consolidated dict instead of a list of objects
        consolidated = {}

        for obj in objects:
            try:
                consolidated.update(obj)
            except ValueError:
                try:
                    consolidated.update(json.loads(obj))
                # # TODO: Should be a JsonDecoderError
                except Exception:  # NOQA
                    consolidated.update(
                        {'_bad_object_{0}'.format(str(uuid.uuid4())): obj})
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
        # This of course means that if any of these are provided
        # within the chain, they will be overriden here.
        log.update({
            'message': message,
            # TODO: declare `upper` method when instantiating class or
            # simply remove it altogether.
            'level': level.upper(),
            # TODO: Maybe we don't need a method here and can directly
            # call the datetime method? Perf-wise, that is..
            'timestamp': self._get_timestamp()
        })

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
        logger_env = os.getenv('WRYTE_{0}_{1}'.format(
            self.logger_name.upper(), variable))
        global_env = os.getenv('WRYTE_{0}'.format(variable))
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

        if self._env('HANDLERS_SYSLOG_ENABLED'):
            self.add_syslog_handler()

        if self._env('HANDLERS_LOGZIO_ENABLED'):
            self.add_logzio_handler()

        if self._env('HANDLERS_FILE_ENABLED'):
            self.add_file_handler()

        if self._env('HANDLERS_ELASTICSEARCH_ENABLED'):
            self.add_elasticsearch_handler()

    def _assert_level(self, level):
        levels = LEVEL_CONVERSION.keys()

        if level.lower() not in levels:
            self.logger.exception('Level must be one of %s', levels)
            return False
        return True

    def add_handler(self,
                    handler,
                    name=None,
                    formatter='json',
                    level='info'):
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
            return

        # TODO: Allow to ignore fields in json formatter
        # TODO: Allow to remove field printing in console formatter
        if formatter == 'json':
            _formatter = JsonFormatter(self.pretty or False)
        elif formatter == 'console':
            if COLOR_ENABLED:
                colorama.init(autoreset=True)
            pretty = True if self.pretty in (None, True) else False
            _formatter = ConsoleFormatter(pretty, self.color, self.simple)
        else:
            _formatter = formatter

        handler.setFormatter(_formatter)
        handler.set_name(name)

        self.logger.addHandler(handler)

        return name

    def list_handlers(self):
        """Return a list of all handlers attached to a logger
        """
        return [handler.name for handler in self.logger.handlers]

    def remove_handler(self, name):
        """Remove a handler by its name (set in `add_handler`)
        """
        for handler in self.logger.handlers:
            if handler.name == name:
                self.logger.removeHandler(handler)

    def add_default_json_handler(self, level='debug'):
        return self.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter='json',
            level=self._env('CONSOLE_LEVEL', level))

    def add_default_console_handler(self, level='debug'):
        name = '_console'
        level = self._env('CONSOLE_LEVEL', default=level)
        formatter = 'console'
        handler = logging.StreamHandler(sys.stdout)

        return self.add_handler(
            handler=handler,
            name=name,
            formatter=formatter,
            level=level)

    def add_file_handler(self, **kwargs):
        if not self._env('HANDLERS_FILE_PATH'):
            self.logger.warn('File handler file path not set')

        name = self._env('HANDLERS_FILE_NAME', default='file')
        level = self._env('HANDLERS_FILE_LEVEL', default='info')
        formatter = self._env('HANDLERS_FILE_FORMATTER', default='json')

        if self._env('HANDLERS_FILE_ROTATE'):
            try:
                max_bytes = int(
                    self._env('HANDLERS_FILE_MAX_BYTES', default=13107200))
                backup_count = int(
                    self._env('HANDLERS_FILE_BACKUP_COUNT', default=7))
            except ValueError:
                self.logger.exception(
                    'MAX_BYTES and BACKUP_COUNT must be integers')
                return

            handler = logging.handlers.RotatingFileHandler(
                self._env('HANDLERS_FILE_PATH'),
                maxBytes=max_bytes,
                backupCount=backup_count)
        elif os.name == 'nt':
            handler = logging.FileHandler(self._env('HANDLERS_FILE_PATH'))
        else:
            handler = logging.handlers.WatchedFileHandler(
                self._env('HANDLERS_FILE_PATH'))

        self.add_handler(
            handler=handler,
            name=name,
            formatter=formatter,
            level=level)

    def add_syslog_handler(self, **kwargs):
        name = self._env('HANDLERS_SYSLOG_NAME', default='syslog')
        level = self._env('HANDLERS_SYSLOG_LEVEL', default='info')
        formatter = self._env('HANDLERS_SYSLOG_FORMATTER', default='json')

        syslog_host = self._env('HANDLERS_SYSLOG_HOST',
                                default='localhost:514')
        syslog_host = syslog_host.split(':', 1)

        if len(syslog_host) == 2:
            # Syslog listener
            host, port = syslog_host
            address = (host, port)
        else:
            # Unix socket or otherwise
            address = syslog_host

        socket_type = self._env('HANDLERS_SYSLOG_SOCKET_TYPE', default='udp')
        if socket_type not in ('tcp', 'udp'):
            self.logger.warn(
                'syslog handler socket type must be one of tcp/udp')

        handler = logging.handlers.SysLogHandler(
            address=address,
            facility=self._env('HANDLERS_SYSLOG_FACILITY', default='LOG_USER'),
            socktype=socket.SOCK_STREAM if socket_type == 'tcp'
            else socket.SOCK_DGRAM)

        self.add_handler(
            handler=handler,
            name=name,
            formatter=formatter,
            level=level)

    def add_logzio_handler(self, **kwargs):
        if LOGZIO_INSTALLED:
            if not self._env('HANDLERS_LOGZIO_TOKEN'):
                self.logger.warn('Logzio handler token not set')

            name = self._env('HANDLERS_LOGZIO_NAME', default='logzio')
            level = self._env('HANDLERS_LOGZIO_LEVEL', default='info')
            formatter = self._env('HANDLERS_LOGZIO_FORMATTER', default='json')
            handler = LogzioHandler(self._env('HANDLERS_LOGZIO_TOKEN'))

            self.add_handler(
                handler=handler,
                name=name,
                formatter=formatter,
                level=level)
        else:
            self.logger.error(
                'It seems that the logzio handler is not installed. '
                'You can install it by running `pip install '
                'wryte[logzio]`')

    def add_elasticsearch_handler(self, **kwargs):
        if ELASTICSEARCH_INSTALLED:
            if not self._env('HANDLERS_ELASTICSEARCH_HOST'):
                self.logger.warn('Elasticsearch handler host not set')

            name = self._env('HANDLERS_ELASTICSEARCH_NAME',
                             default='elasticsearch')
            level = self._env('HANDLERS_ELASTICSEARCH_LEVEL', default='info')
            formatter = self._env(
                'HANDLER_ELASTICSEARCH_FORMATTER', default='json')

            hosts = []
            es_hosts = self._env('HANDLERS_ELASTICSEARCH_HOST')
            es_hosts = es_hosts.split(',')
            for es_host in es_hosts:
                host, port = es_host.split(':', 1)
                hosts.append({'host': host, 'port': port})

            handler_args = {
                'hosts': hosts,
                'auth_type': CMRESHandler.AuthType.NO_AUTH
            }

            handler = CMRESHandler(**handler_args)

            self.add_handler(
                handler=handler,
                name=name,
                formatter=formatter,
                level=level)
        else:
            self.logger.error(
                'It seems that the elasticsearch handler is not installed. '
                'You can install it by running `pip install '
                'wryte[elasticsearch]`')

    def set_level(self, level):
        """Set the current logger instance's level.
        """
        # TODO: Consider removing this check and letting the user
        # take the hit incase they provide an unreasonable level.
        # This would reduce overhead when using `set_level` in
        # error messages under heavy load.
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
        """Unbind previously bound context.
        """
        # TODO: Support unbinding nested field in context
        for key in keys:
            self._log.pop(key)

    def event(self, message, *objects, **kwargs):
        """Log an event and return a cid for it.

        Once an event is fired, a `cid` is generated for it unless
        explicitly passed in kwargs. Additionally, the `type` of the
        log will be `event`, instead of log, like in other cases.
        """
        # TODO: Prefix cid key with underscore
        cid = kwargs.get('cid', str(uuid.uuid4()))
        # TODO: Consider allowing to bind `cid` here.
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
        if kwargs.get('_set_level'):
            self.set_level(kwargs.get('_set_level'))

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
        if kwargs.get('_set_level'):
            # TODO: Use subscriptiong instead
            self.set_level(kwargs.get('_set_level'))
            # TODO: Don't pop, this could be useful in the log
            kwargs.pop('_set_level')
        obj = self._enrich(message, 'error', objects, kwargs)
        self.logger.error(obj)

    def critical(self, message, *objects, **kwargs):
        if kwargs.get('_set_level'):
            # TODO: Use subscriptiong instead
            self.set_level(kwargs.get('_set_level'))
            # TODO: Don't pop, this could be useful in the log
            kwargs.pop('_set_level')
        obj = self._enrich(message, 'critical', objects, kwargs)
        self.logger.critical(obj)


class WryteError(Exception):
    pass


if CLI_ENABLED:
    CLICK_CONTEXT_SETTINGS = dict(
        help_option_names=['-h', '--help'],
        token_normalize_func=lambda param: param.lower())

    @click.command(context_settings=CLICK_CONTEXT_SETTINGS)
    @click.argument('LEVEL')
    @click.argument('MESSAGE')
    @click.argument('OBJECTS', nargs=-1)
    @click.option(
        '--pretty/--ugly',
        is_flag=True,
        default=True,
        help='Output JSON instead of key=value pairs for console logger')
    @click.option(
        '-j',
        '--json',
        'jsonify',
        is_flag=True,
        default=False,
        help='Use the JSON logger formatter instead of the console one')
    @click.option(
        '-n',
        '--name',
        type=click.STRING,
        default='Wryte',
        help="Change the default logger's name")
    @click.option(
        '--no-color',
        is_flag=True,
        default=False,
        help='Disable coloring in console formatter')
    @click.option(
        '--simple',
        is_flag=True,
        default=False,
        help='Log only message to the console')
    def main(level, message, objects, pretty, jsonify, name, no_color, simple):
        wryter = Wryte(
            name=name,
            pretty=pretty,
            level=level,
            jsonify=jsonify,
            color=not no_color,
            simple=simple)
        getattr(wryter, level.lower())(message, *objects)
else:
    def main():
        sys.exit(
            "To use Wryte's CLI you must first install certain dependencies. "
            "Please run `pip install wryte[cli]` to enable the CLI.")
