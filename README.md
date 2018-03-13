Wryte
=====

[![Travis Build Status](https://travis-ci.org/nir0s/wryte.svg?branch=master)](https://travis-ci.org/nir0s/wryte)
[![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/kuf0x8j62kts1bpg/branch/master?svg=true)](https://ci.appveyor.com/project/nir0s/wryte)
[![PyPI Version](http://img.shields.io/pypi/v/wryte.svg)](http://img.shields.io/pypi/v/wryte.svg)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/wryte.svg)](https://img.shields.io/pypi/pyversions/wryte.svg)
[![Requirements Status](https://requires.io/github/nir0s/wryte/requirements.svg?branch=master)](https://requires.io/github/nir0s/wryte/requirements/?branch=master)
[![Code Coverage](https://codecov.io/github/nir0s/wryte/coverage.svg?branch=master)](https://codecov.io/github/nir0s/wryte?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/91979a5f607429443e4f/maintainability)](https://codeclimate.com/github/nir0s/wryte/maintainability)
[![Code Quality](https://landscape.io/github/nir0s/wryte/master/landscape.svg?style=flat)](https://landscape.io/github/nir0s/wryte)
[![Is Wheel](https://img.shields.io/pypi/wheel/wryte.svg?style=flat)](https://pypi.python.org/pypi/wryte)

Note that the following documentation relates to the code currently in the master branch. If you want to view docs for previous versions, please choose the relevant release in the "releases" tab.

## Features

Wryte aims to provide a simple API for logging in Python:

* Very easy to get started
* Sane defaults!
* Easily configurable via env vars (for the purpose of easy config via schedulers e.g. systemd, nomad, k8s)
* Standardize formatting for both Console (human readable) and aggregation (JSON)
* Handler agnosticism
* Differentiate user events and system logs
* Auto-enrich with useful data (hostname, pid, etc..)
* Easily provide contexual data
* Dynamic severity levels
* Context binding to prevent repetition
* Retroactive logging (WIP)
* Assist in user tracing (via auto-provided context ids)
* Zero exceptions. There should be zero logging exceptions causing the app to crash but rather Wryte should log errors whenever logging errors occur.

The main premise is that a standard CLI application logs to the console, while a server side app will probably want to log some human readable messages to syslog/console while logging JSON containing the same information with some additional contextual information over the wire (to a log aggregation backend e.g. ELK/Graylog2)



## Installation

Wryte supports Linux, Windows and OSX on Python 2.7 and 3.4+

```shell
pip install wryte
pip install wryte[color] # for colored console output.
```

For dev:

```shell
pip install https://github.com/nir0s/wryte/archive/master.tar.gz
```

## Usage

### Getting Started

```python
from wryte import Wryte

wryter = Wryte(name='app')
wryter.info('My Message')

# 2017-12-22T17:02:59.550920 - app - INFO - my message
...

```

### CLI

Wryte provides a basic CLI to show-off output.

```
$ pip install wryte[cli]

$ wryte -h
Usage: wryte [OPTIONS] LEVEL MESSAGE [OBJECTS]...

Options:
  --pretty / --ugly  Output JSON instead of key=value pairs for console logger
  -j, --json         Use the JSON logger formatter instead of the console one
  -n, --name TEXT    Change the default logger's name
  --no-color         Disable coloring in console formatter
  --simple           Log only message to the console
  -h, --help         Show this message and exit.

# Examples:

$ wryte event my-event
2018-02-18T08:52:23.526820 - Wryte - EVENT - my-event
  cid=49b9260c-77b8-4ebb-bb15-d6ccce7c7ba4

$ wryte info my-message key1=value1 key2=value2
2018-02-18T08:52:50.691206 - Wryte - INFO - my-message
  key1=value1
  key2=value2

$ wryte info my-message key1=value1 key2=value2 --ugly
2018-02-18T08:53:45.126228 - Wryte - INFO - my-message
{
    "key2": "value2",
    "key1": "value1"
}

$ wryte info my-message key1=value1 key2=value2 -j
{
    "key1": "value1",
    "name": "Wryte",
    "pid": 18613,
    "type": "log",
    "level": "INFO",
    "timestamp": "2018-02-18T08:53:06.222926",
    "message": "my-message",
    "hostname": "nir0s-x1",
    "key2": "value2"
}

```

### Instantiating the logger

```python
from wryte import Wryte

wryter = Wryte(
  name=None,  # The name of the logger (appended to each log message)
  hostname=None,  # The hostname
  level='info',  # severity level
  pretty=None,  # (Console only) Whether to pretty-print JSON
  bare=False,  # Omit any default handlers. You will have to add them yourself after.
  jsonify=False,  # (Console only) Output json to the console instead of a human readable message.
  color=True,  # (Console only) Colorize Console output.
  simple=False  # (Console only) Only print the message and key=value pairs.
)
```

### Available logging levels

Wryte supports the following logging levels:

* `event` (see below)
* `debug`
* `info`
* `warning`
* `warn`
* `error`
* `critical`

### Distinguishing Events from Logs

Events are logs generated by user interactions, while logs are contextual to them. e.g.:

```python
wryter.event('Logging user in', user_id=user.id)
wryter.info('Retrieving user info...' user_id=user.id)
wryter.debug('Requesting session...', ...)
# more debug stuff..
wryter.info('User Logged in!', user_id=user.id)
```

Wryte explicitly provides an `event` method so that you're able to distinguish "things that happened in my application" from "things that happened in my system".

An event is technically distinguished from a log by having a `{ 'type': 'event' }` field and different coloring in the console as well as returning a `cid` for flow tracing (more on that later).

### Wryting a simple log to the console

By default, Wryte will output `TIMESTAMP - LEVEL - LOGGER_NAME - MESSAGE` (and the provided key=value pairs) to the console. Many CLI applications log only the message (e.g. `pip`). You can configure Wryte to do so by either setting the `WRYTE_SIMPLE_CONSOLE` env var or by passing the `simple` flag when instantiating the logger:

```python
wryter = Wryte(simple=True)
wryter.info('My Message')
>>> 'My Message'
```

### Logging to both the console (journald, stdout, etc..) and an aggregation backend

An interesting use-case is when you want to provide easy server-side debugging using human readable messages while also sending events and logs to an aggregation backend such as Elasticsearch, Graylog2 and the likes.

For example:

```python
from logzio.handler import LogzioHandler

# Instantiate a debug level console logger named `wryte`.
wryter = Wryte(name='wryte', level='debug')
# `formatter` default is `json`. `level` default is `info`.
wryter.add_handler(handler=LogzioHandler('LOGZIO_TOKEN'), name='logzio', formatter='json', level='info')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'key3=value3')
# 2017-12-22T17:02:59.550920 - app - INFO - my message
#  key1=value1,
#  key2=value2,
#  who=where

...

# This is sent to logz.io
# {
#     "timestamp": "2017-12-22T14:19:09.828625"
#     "hostname": "nir0s-x1",
#     "level": "DEBUG",
#     "message": "TEST_MESSAGE",
#     "pid": 8554,
#     "name": "wryte",
#     "key1": "value1",
#     "key2": "value2",
#     "key3": "value3",
# }
```

The above will log the message and its associated key value pairs to the console in a human readable format and log machine readable JSON with some additional contextual information to logz.io.


### Adding Context

On top of logging simple messages, Wryte assumes that you have context you would like to add to your logs.
Instead of making you work to consolidate your data, Wryte allows you to pass multiple dictionaries and key value pair strings and consolidate them to a single dictionary.

You can pass any number of single level or nested dictionaries and `key=value` strings or kwargs and even JSON strings, and those will be parsed and added to the log message.

For example:

```python
wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')
# 2017-12-22T17:02:59.550920 - app - INFO - my message
#  key1=value1,
#  key2=value2,
#  who=where

wryter.error('Logging kwargs', key='value')  # kwargs
wryter.debug('Logging JSON strings', '{"key": "value"}')  # JSON strings
wryter.critical('Logging nested dicts', {'key': 'value', 'nested': { 'key1': 'value1', 'key2': 'value2'}})

```

#### Reserved Fields

The following are fields reserved to Wryte:

* Any `_field`
* `hostname`
* `pid`
* `message`
* `timestamp`
* `level`
* `type`
* `name`

Note that even if the fields are provided in a log message, they are bound to be overriden by Wryte.


#### Binding contextual information to a logger

To prevent having to repeat context with every log message, Wryte allows you to bind any amount of key=value pairs to a logger to add context to it.

Until unbound, the logger will include the bound fields in each message.

```python
wryter = ...
wryter.info('This will add the above key value pairs to any log message')
wryter.bind({'user_id': framework.user, ...}, key=value)
# ...do stuff

wryter.unbind('user_id')
```

And just like with the logger itself, you can bind nested dicts, kwargs, json strings and kv pair strings.

### Changing a logger's level

To better control output

You can change a logger's level like so:

```python
wryter.set_level(LEVEL_NAME)
```

#### Dynamically changing log level on errors

Debug logs are only interesting when we need to debug something. Logging can potentially block the application (if not using asnyc handlers), utilize the network, or increase disk IOPS. Ideally, we would only handle debug logs when some problem arises, and once that is resolved, the logger will assume info level logging.

You can signal that a certain error requires changing the level to "debug" from now on. You could use the `set_level` method everytime you have such an error but instead, Wryte proposes that it should simpler.

For example, let's say that your application reads a config file per `gunicorn` worker and you would like to activate debug logging if for some reason a worker can't read the file:

```python
config_file_read = False

try:
    config = read_config(PATH)
except ReadError as ex:
    # Can also pass `set_level` to `critical`, not just to `error`.
    wryter.error('Failed to read config ({})'.format(ex), {'context': context}, _set_level='debug')
    # do_something to reread the file, but this time with debug logging enabled.
    config_file_read = True
finally:
    if config_file_read:
        wryter.set_level('info')
    else:
        raise SomeError(...)

```

Dumb example maybe, but you get the point :)

The `_set_level` flag is supported in the `error` and `critical` severity levels.


### Retroactive Logging

`raise NotImplementedError('WIP!')` :)

Much like dynamic level logging, retroactive logging can help reduce strain on the application/server by only logging to disk/network when there's a certain problem.

Retroactive logging is the practice of logging all transaction-specific logs to memory and only flushing to disk/ over the wire if something goes wrong; otherwise, we simply get rid of them. A culprit of this is that if the application stops working, it won't write the logs.

Wryte aims to provide a retroactive logging implementation somewhere along the lines of:

```python
wryter.event('...', _retro=True)
# from here on, until the end of a transaction, all debug logs will be logged to the MemoryHandler
wryter.debug('...')
...

# End of transaction. If err, write, else, flush to Null.
wryter.flush(err)

```


### Instantiating a bare Wryte instance

You can instantiate a logger without any handlers and add handlers yourself.

Note that if you instantiate a bare logger, logging will succeed but you will not get any output.
Wryte doesn't protect you from doing that simply because you might want to add handlers only in specific situations.

```python
import logging

wryter = Wryte(name='wryte', level='debug', bare=True)
wryter.add_handler(handler=logging.FileHandler('file.log'), formatter='console')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, who=where)

with open('file.log') as log_file:
    print(log_file.read())
...

```

### Listing and removing handlers

You can list and remove handlers currently attached to a logger:

```python
import logging

wryter = Wryte()
handler_name = wryter.add_handler(
    handler=logging.FileHandler('file.log'),
    formatter='console')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, who=where)
# ...log some more

wryter.list_handlers()
['777b9655-e6f9-4b90-8be9-730edeb3afcf', '_console']
wryter.remove_handler(handler_name)
```

By default the `_json` or `_console` handlers are added and they can also be removed.

### Using Formatters

Currently, Wryte allows to choose between just two formatters: `json` and `console`. The `json` formatter obviously doesn't require any formatting as any fields provided in the message will be propagated with the JSON string.

The console output, on the other hand, might require formatting. Wryte's priority is to simplify and standardize the way we print and ship log messages, not to allow you to just view console logs anyway you want. I might add something in the future to allow to format console messages.

To make sure you can still print out messages formatted the way you want, without utilizing `Wryte`, you can simply pass your formatter instance when adding a handler, e.g:

```python
import logging

wryter = Wryte(name='wryte', level='debug', bare=True)
wryter.add_handler(handler=logging.StreamHandler(sys.stdout), formatter=myFormatter)

```

### Coloring

The Console formatter supplied by Wryte outputs a colorful output by default using colorama, if colorama is installed.

The severity levels will be colored differently accordingly to the following mapping:

```bash
$ pip install wryte[color]
```

```python
mapping = {
    'debug': Fore.CYAN,
    'info': Fore.GREEN,
    'warning': Fore.YELLOW,
    'warn': Fore.YELLOW,
    'error': Fore.RED,
    'critical': Style.BRIGHT + Fore.RED
}
```

You can disable colored output by instantating your logger like so:

```python
wryter = Wryte(color=False)
```

### Flow Tracing and context ID's

Ideally, when a user performs an action in an app, a context related to that event will be logged and attached to any log message relating to that event, so that it is possible to tail the entire flow from the moment the user performed the action and until, say, they got a response from the db. Woo! What a long sentence!

This feature is not provided by any logging library that I know of, and for a good reason - it depends on many factors potentially related to that specific app. `structlog`, for instance, provides a way to log using a thread-local context, but that's specific to a thread and therefore doesn't solve the problem for distributed systems.
A good way to solve the problem is to use a global, cross-service identifier (for instance, a user id).

Specifically for non-distributed systems, you can use the `cid` generated by the `event` method and supply it as an identifier.

```python
# cid defaults to a uuid if it isn't provided.
cid = wryter.event('User logging in', {'user_id': 'nir0s'}, cid=user.id)
wryter.bind(cid=cid)
wryter.debug('Requesting log-in host...', ...)
...
wryter.debug('Querying db for available server...', ...)
...
wryter.info('Host is: {0}'.format(host_ip))
wryter.unbind('cid')
...
```

The idea behind this is that a cid can be passed into any log message within the same context. "within the same context" is of course very abstract, and is up to the developer to implement as it might be thread-related, framework-related, or else. I intend to expand the framework, but for now, that's what it is.

### Accessing lower-level logger API

Wryte is built on top of Python's standard `logging` library and you can access the logger's API directly:

```python
wryter = Wryte()

wryter.logger.setLevel(...)
current_level = wryter.logger.getEffectiveLevel(...)
...

```

The idea behind this is three-fold:

1. You shouldn't need to use `logging` directly, because why would you?
2. You should be able to workaround anything not implemented by Wryte, because reality.
3. For the sake of keeping Wryte as minimal as possible, some things will not be implemented in Wryte and you will be able to use the logger's API directly so that you're not limited.

## Configuring Wryte

### Using Environment Variables to configure logging handlers

NOTE: This is WIP, so things may break / be broken.

One of Wryte's goals is to provide a simple way to configure loggers. Much like Grafana and Fabio, Wryte aims to be completely env-var configurable.

On top of having two default `console` and `json` handlers which indicate the formatting and both log to stdout, you can utilize built-in and 3rd party handlers quite easily.

Below are the global env vars used to configure all loggers instantiated by Wryte.
If you want to apply a handler to a specific logger, use the `WRYTE_$LOGGER_NAME_HANDLERS_*` pattern instead (e.g. `WRYTE_WEBLOGGER_HANDLERS_FILE_ENABLED` - all uppercase).

For each handler, there are four basic env vars:

* `WRYTE_HANDLERS_TYPE_ENABLED`   -> Enables the handler if set
* `WRYTE_HANDLERS_TYPE_NAME`      -> The handler's name (defaults to `TYPE` in lowercase)
* `WRYTE_HANDLERS_TYPE_LEVEL`     -> The handler's logging level (defaults to `info` unless explicitly stated otherwise)
* `WRYTE_HANDLERS_TYPE_FORMATTER` -> The handler's formatter (`json` or `console`, defaults to `json`)

On top of those, there are handler specific configuration options:

#### FILE Handler

Wryte supports both the rotating and watching file handlers (on Windows, FileHandler replaces WatchingFileHandler if not rotating).

```
# (Required) Absolute path to the file logs should be written to
export WRYTE_HANDLERS_FILE_PATH=FILE_TO_LOG_TO

# If set, will rotate files.
export WRYTE_HANDLERS_FILE_ROTATE=false

# Size of each file in bytes if rotating
export WRYTE_HANDLERS_FILE_MAX_BYTES=13107200

# Amount of logs files to keep if rotating
export WRYTE_HANDLERS_FILE_BACKUP_COUNT=7
```

#### SYSLOG Handler

Allows to emit logs to a Syslog server

```
# Colon separated syslog host string
export WRYTE_HANDLERS_SYSLOG_HOST='localhost:514'

export WRYTE_HANDLERS_SYSLOG_SOCKET_TYPE='udp'  # udp/tcp

# Syslog facility to use (see https://success.trendmicro.com/solution/TP000086250-What-are-Syslog-Facilities-and-Levels)
export WRYTE_HANDLERS_SYSLOG_FACILITY='LOG_USER'
```

#### ELASTICSERACH Handler

While it may be useful to send your messages through logstash, you may also log to Elasticsearch directly.

Wryte utilizes the [CMRESHandler](https://github.com/cmanaha/python-elasticsearch-logger) for this.
Currently, only the hosts can be supplied. SSL, index name pattern, etc.. will be added later.

To install the handler, run `pip install wryte[elasticsearch]`.

```
# (Required) A comma-separated list of host:port pairs to use.
export WRYTE_HANDLERS_ELASTICSEARCH_HOST=http://es.dc1.service.consul:9200,http://es.dc1.service.consul:9200
```

#### LOGZIO Handler

You can also directly send your logs to logzio via the official [logzio handler](https://github.com/logzio/logzio-python-handler).

To install the handler, run `pip install wryte[logzio]`.

```
# (Required) Your logzio API token
export WRYTE_HANDLERS_LOGZIO_TOKEN=oim12o3i3ou2itj3jkdng3bgjs1gbg
```

See https://github.com/nir0s/wryte/issues/10 and https://github.com/nir0s/wryte/issues/18 for more info.

#### Examples

Logging to file:

```
$ export WRYTE_HANDLERS_FILE_ENABLED=true
$ export WRYTE_HANDLERS_FILE_PATH=log.file

$ python wryte.py
2018-02-18T08:56:27.921500 - Wryte - INFO - Logging an error level message:
2018-02-18T08:56:27.921898 - Wryte - ERROR - w00t
2018-02-18T08:56:27.922055 - Wryte - INFO - Logging an event:
2018-02-18T08:56:27.922259 - Wryte - EVENT - w00t
  cid=5e7bbc8e-5857-4934-9a21-d134a8086319
2018-02-18T08:56:27.922421 - Wryte - INFO - Binding more dicts to the logger:
2018-02-18T08:56:27.922623 - Wryte - INFO - bind_test
  bound1=value1
  bound2=value2
2018-02-18T08:56:27.922783 - Wryte - INFO - Unbinding keys:
  bound1=value1
  bound2=value2
2018-02-18T08:56:27.922935 - Wryte - CRITICAL - unbind_test
  bound2=value2
2018-02-18T08:56:27.923088 - Wryte - ERROR - w00t
  bound2=value2

$ cat log.file
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.921500", "hostname": "my-host", "pid": 19220, "type": "log", "message": "Logging an error level message:"}
{"name": "Wryte", "level": "ERROR", "timestamp": "2018-02-18T08:56:27.921898", "hostname": "my-host", "pid": 19220, "type": "log", "message": "w00t"}
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.922055", "hostname": "my-host", "pid": 19220, "type": "log", "message": "Logging an event:"}
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.922259", "hostname": "my-host", "pid": 19220, "message": "w00t", "type": "event", "cid": "5e7bbc8e-5857-4934-9a21-d134a8086319"}
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.922421", "hostname": "my-host", "pid": 19220, "type": "log", "message": "Binding more dicts to the logger:"}
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.922623", "bound1": "value1", "hostname": "my-host", "pid": 19220, "message": "bind_test", "type": "log", "bound2": "value2"}
{"name": "Wryte", "level": "INFO", "timestamp": "2018-02-18T08:56:27.922783", "bound1": "value1", "hostname": "my-host", "pid": 19220, "message": "Unbinding keys:", "type": "log", "bound2": "value2"}
{"name": "Wryte", "bound2": "value2", "message": "unbind_test", "level": "CRITICAL", "timestamp": "2018-02-18T08:56:27.922935", "hostname": "my-host", "pid": 19220, "type": "log"}
{"name": "Wryte", "bound2": "value2", "message": "w00t", "level": "ERROR", "timestamp": "2018-02-18T08:56:27.923088", "hostname": "my-host", "pid": 19220, "type": "log"}

```

## Performance

I haven't performed a deep benchmark on Wryte yet and am waiting to finish an initial implementation I will feel comfortable with before doing so.

A very shallow benchmark (on my i7 1st Gen x1-carbon) showed:

(For 10000 messages averaged over 30 runs, coloring disabled):

`log.info('My Message')`

* Wryte     -> 407ms
* Logbook   -> 479ms
* structlog -> 750ms
* logging   -> 279ms

Not bad. I'll be optimizing for performance wherever possible.

## Testing

```shell
git clone git@github.com:nir0s/wryte.git
cd wryte
pip install tox
tox
```
