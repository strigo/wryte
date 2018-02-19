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


NOTE: WIP! Consider some of the features below as experimental.
NOTE: Performance is literally on the bottom of my priorities right now. I haven't tested how performant wryte is, and will only do so when I feel I've covered basic functionality.


Wryte aims to provide a simple API for logging in Python for both human readable and JSON messages.

The main premise is that a standard CLI application logs to the console, while a server side app will probably want to log some human readable messages to syslog/console while logging JSON strings containing the same information with some additional contextual information over the wire (to a log aggregation service e.g. ELK/Graylog2)

Note that the following documentation relates to the code currently in the master branch. If you want to view docs for previous versions, please choose the relevant release in the "releases" tab.

Anyway, getting started is as easy as:

```python
from wryte import Wryte

wryter = Wryte(name='app')
wryter.info('My Message')
2017-12-22T17:02:59.550920 - app - INFO - my message
...

```

## Design principles:

* Very easy to get started.
* Standardize for both human readable and machine readable strings for console output and server aggregation OOB with almost zero config.
* Handler agnostic - you will be able to pass whichever handlers you desire.
* While also providing default implementations for the most common handlers.
* Auto-enrich with basic metadata (e.g. hostname, pid, etc..) so that the user doesn't have to.
* Single transportable module with (by default) no non-stdlib dependencies. (For now, for development purposes, Click is required to test via Wryte's CLI)
* Make it easy to consolidate different parts of the log message.


## Alternatives

Without getting into too much detail:

* `structlog` is by far the best logger I've found up until now, but is not as simple as I'd like it to be when trying to provide the most standardized way of logging.
* `pygogo` is nice but (like structlog) is too low-level for prodiving a standardized logging methodology.
* `logbook` is extremely configurable, but again, not simple enough for standardization.

Just to clarify, the aforementioned logging libraries are awesome, and can provide for anyone (certainly much better than `wryte` would for complex scenarios). While I would happily use any of them, they are built to let people "do whatever the hell they want". From my POV, they're missing three things:

* Being easily configurable via ENV VARS for both formatting and shipping.
* Sane defaults(!) for formatting (JSON to aggregate, readable for console), no bullshit.
* Simplifying handler configuration - i.e. most Python loggers provide very robust formatting configuration, while relatively neglecting handler ease-of-use (even `logbook`, which provides configurable 3rd party handlers doesn't have sane defaults.)

To sum up, what I would EVENTUALLY (it may take time) like to provide the user with is the following workflow (e.g.):

```
export WRYTE_logger_name_ENDPOINT_TYPE=elasticsearch
export WRYTE_logger_name_ELASTICSEARCH_ENDPOINT=http://my-elastic-cluster:9200
export WRYTE_logger_name_ELASTICSEARCH_SSL ...
...

wryter.info('Message', {'x':'y'})
```

This, alone, should write a human readable log to console and a JSON message to Elasticsearch.


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

### CLI

Wryte provides a basic CLI to show-off output. You can utilize it by first installing the required dependencies:

```
$ pip install wryte[cli]
$ wryte -h
Usage: wryte [OPTIONS] LEVEL MESSAGE [OBJECTS]...

Options:
  --pretty / --ugly  Output JSON instead of key=value pairs for console logger
  -j, --json         Use the JSON logger formatter instead of the console one
  -n, --name TEXT    Change the default logger's name
  --no-color         Disable coloring in console formatter
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


### Logging JSON strings

It will be often that you would simply want to log JSON strings (for instance, when you log to Elasticsearch or any other document store).

While Wryte uses a special formatter to create that JSON string, you can just use the `jsonify` flag when instantiating the logger instance. On top of spitting out JSON, it will also add some potentially interesting contexual information (which might be a tad less interesting in the console) like the `hostname` and the `pid`.

```python

wryter = Wryte(name='wryte', pretty=True, level='debug', jsonify=True)
wryter.debug('TEST_MESSAGE', {'port': '8121'}, 'ip=127.0.0.1')
{
    "timestamp": "2017-12-22T14:19:09.828625"
    "level": "DEBUG",
    "message": "TEST_MESSAGE",
    "pid": 8554,
    "hostname": "nir0s-x1",
    "name": "wryte",
    "ip": "127.0.0.1",
    "port": "8121",
}
```

### Adding key=value pairs

On top of logging simple messages, Wryte assumes that you have context you would like to log.
Instead of making you work to consolidate your data, Wryte allows you to pass multiple dictionaries and key value pair strings and consolidate them to a single dictionary.

You can pass any number of single level or nested dictionaries and `key=value` strings and even JSON strings, and those will be parsed and added to the log message.

```python
wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')
2017-12-22T17:02:59.550920 - app - INFO - my message
  key1=value1,
  key2=value2,
  who=where
```

#### Binding contextual information to a logger

You can bind any amount of key=value pairs to a logger to add context to it:

```python
wryter = ...
wryter.info('This will add the above key value pairs to any log message')
wryter.bind({'user_id': framework.user, ...}, 'key=value')
# ...do stuff

wryter.unbind('user_id')
```

### Using a different handler

The previous examples might not be that interesting because by default, Wryte uses Python's `logging.StreamHandler` configuration to print to `stdout`.

What might be more interesting, is to use a handler which sends the logs somewhere else. Let's take the logz.io Handler found at https://github.com/logzio/logzio-python-handler for example.

The following will log the message and its associated key value pairs to the console in a human readable format and log a machine readable JSON string with some additional contextual information to logz.io.

```python
from logzio.handler import LogzioHandler

# Instantiate a debug level console logger named `wryte`.
wryter = Wryte(name='wryte', level='debug')
# `formatter` default is `json`. `level` default is `info`.
wryter.add_handler(handler=LogzioHandler('LOGZIO_TOKEN'), name='logzio', formatter='json', level='info')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'key3=value3')
2017-12-22T17:02:59.550920 - app - INFO - my message
  key1=value1,
  key2=value2,
  who=where

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

### Using env vars to configure logging handlers

One of Wryte's goals is to provide a simple way to configure loggers.

A POC currently exists for using environment variables to enable certain handlers:

```bash
export WRYTE_FILE_PATH=PATH_TO_OUTPUT_FILE
export WRYTE_LOGZIO_TOKEN=YOUR_LOGZIO_TOKEN

export WRYTE_ELASTICSEARCH_HOST
export WRYTE_ELASTICSEARCH_PORT (defaults to 9200)
export WRYTE_ELASTICSEARCH_INDEX (defaults to `logs`)
```

Will automatically append `json` formatted handlers to any logger you instantiate.
Of course, this should be configurable on a logger level so, when this is done, it should provide something like:

```
export WRYTE_logger_name_FILE_PATH=...
export WRYTE_logger_name_LOGZIO_TOKEN=...
```

Eventually, I intend to have Wryte be fully configurable via env vars.

See https://github.com/nir0s/wryte/issues/10 for more info.

Example:

```
$ export WRYTE_FILE_PATH=log.file

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

### Setting a level post-init?

Changing the logger's level is easy:

```python
wryter.set_level(LEVEL_NAME)
```

### Dynamically changing log level on errors

In a production environment, debug level logging is "frowned upon" (in a very general sense, of course).

You can change the log level of a logger anytime (see above). In case of errors, though, you might want to signal that a certain error requires changing the level to "debug" from now on. You could use the `set_level` method everytime you have such an error but instead, Wryte proposes that it should simpler.

For example, let's say that your application reads a config file per `gunicorn` worker and you would like to activate debug logging if for some reason a worker can't read the file:

```python
config_file_read = False

try:
    config = read_config(PATH)
except ReadError as ex:
    # Can also pass `set_level` to `critical`, not just to `error`.
    wryter.error('Failed to read config ({})'.format(ex), {'context': context}, set_level='debug')
    # do_something to reread the file, but this time with debug logging enabled.
    config_file_read = True
finally:
    if config_file_read:
        wryter.set_level('info')
    else:
        raise SomeError(...)

```

Dumb example maybe, but you get the point :)


### Instantiating a bare Wryte instance

You can instantiate a logger without any handlers and add handlers yourself.

Note that if you instantiate a base logger without any handlers, logging will succeed but you will not get any output.
Wryte doesn't protect you from doing that simply because you might want to add handlers only in specific situations.

```python
import logging

wryter = Wryte(name='wryte', level='debug', bare=True)
wryter.add_handler(handler=logging.FileHandler('file.log'), formatter='console')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')

with open('file.log') as log_file:
    print(log_file.read())
...

```

### Listing and removing handlers

Sometimes, you want to add and remove logger handlers dynamically. For instance, let's say that you identified that your application is doing way too many iops on the local disk when logging to a file. You can automatically identify that and remove the file handler and then add it once everything is ok.

You can list and remove handlers currently attached to a logger:

```python
import logging

wryter = Wryte()
handler_name = wryter.add_handler(
    handler=logging.FileHandler('file.log'),
    formatter='console')

wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')
# ...log some more

wryter.list_handlers()
['777b9655-e6f9-4b90-8be9-730edeb3afcf', '_console']
wryter.remove_handler(handler_name)
```

By default the `_json` or `_console` handlers are added and they can also be removed.

## Formatters

Currently, Wryte allows to choose between just two formatters: `json` and `console`. The `json` logger obviously doesn't require any formatting as any fields provided in the message will be propagated with the JSON string.

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

## Contextual logging

In an ideal world, when a user performs an action in an app, a context related to that event will be logged and attached to any log message relating to that event, so that it is possible to tail the entire flow from the moment the user performed the action and until, say, they got a response from the db. Woo! What a long sentence!

This, unfortunately, is not provided by any logging library that I know of, and for a good reason - it depends on many factors potentially related to that specific app.

```python
# cid defaults to a uuid if it isn't provided.
cid = wryter.event('User logging in', {'user_id': 'nir0s'}, cid=user_id)
wryter.bind(cid)
wryter.debug('Requesting log-in host...', ...)
...
wryter.debug('Querying db for available server...', ...)
...
wryter.info('Host is: {0}'.format(host_ip))
wryter.unbind('cid')
...
```

The idea behind this is that a cid can be passed into any log message within the same context. "within the same context" is a very abstract defintion, and is up to the developer to implement as it might be thread-related, framework-related, or else. I intend to expand the framework, but for now, that's what it is.

## Testing

```shell
git clone git@github.com:nir0s/wryte.git
cd wryte
pip install tox
tox
```
