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


NOTE: WIP!

Wryte aims to provide a simple API for logging in Python for both human readable and JSON based messages.

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
* Handler agnostic - you will be able to pass whichever handlers you desire.
* While also providing default implementations for the most common handlers.
* Auto-enrich with basic metadata (e.g. hostname, pid, etc..) so that the user doesn't have to.
* Support both human readable and machine readable strings for console output and server aggregation OOB.
* Single transportable module with (by default) no non-stdlib dependencies. (For now, for development purposes, Click is required to test via Wryte's CLI)
* Make it easy to consolidate different parts of the log message.


## Alternatives

Without getting into too much detail:

* `structlog` is by far the best logger I've found up until now, but is not as simple as I'd like it to be when trying to provide the most standardized way of logging.
* `pygogo` is nice but (like structlog) is too low-level for prodiving a standardized logging methodology.
* `logbook` is extremely configurable, but again, not simple enough for standardization.

## Goal

Just to clarify, the aforementioned logging libraries are awesome, and can provide for anyone (certainly much better than `wryte` would for complex scenarios). While I would happily use any of them, they are build to let people "do whatever the hell they want". From my POV, they're missing three main attributes:

* Easily configurable via ENV VARS for both formatting and shipping.
* Provide sane defaults for formatting (JSON to aggregate, readable for console).
* Simplify handler configuration - i.e. most Python loggers provide very robust formatting configuration, while relatively neglecting handler ease-of-use (even `logbook`, which provides configurable 3rd party handlers don't have sane defaults.)

To sum up, what I would EVENTUALLY (it may take time) like to provide the user is with the following workflow (e.g.):

```
export WRYTE_logger_name_ENDPOINT_TYPE=elasticsearch
export WRYTE_logger_name_ELASTICSEARCH_ENDPOINT=http://my-elastic-cluster:9200
export WRYTE_logger_name_ELASTICSEARCH_SSL ...
...

wryter.info('Message', {'x':'y'})
```

This, alone, should write a readable log to console and a JSON message to elasticsearch.


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


### Adding key=value pairs

On top of logging simple messages, Wryte assumes that you have context you would like to log.
Instead of making you work to consolidate your data, Wryte will allow you to pass multiple dictionaries and key value pair strings and consolidate them to a single dictionary.

You can pass any number of single level or nested dictionaries and `key=value` strings and even JSON strings, and those will be parsed and added to the log message.

```python
wryter.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')
2017-12-22T17:02:59.550920 - app - INFO - my message
  key1=value1,
  key2=value2,
  who=where
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

### Setting a level post-init?

Changing the logger's level is easy:

```python
wryter.set_level(LEVEL_NAME)
```

### Using a different handler

The previous example might not be that interesting because by default, Wryte uses Python's `logging.StreamHandler` configuration to print to `stdout`.

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

Currently, Wryte allows to provide just two formatters: `json` and `console`. The `json` logger obviously doesn't require any formatting as any fields provided in the message will be propagated with the JSON string.

The console output, on the other hand, might require formatting. Wryte's priority is to simplify and standardize the way we print and ship log messages, not to allow you just view console logs anyway you want. I might add something in the future to allow to format console messages.

To make sure you can still print out messages formatted the way you want, without utilizing `Wryte`, you can simply pass your formatter instance when adding a handler, e.g:

```python
import logging

wryter = Wryte(name='wryte', level='debug', bare=True)
wryter.add_handler(handler=logging.StreamHandler(sys.stdout), formatter=myFormatter)

```

### Coloring

The Console formatter supplied by Wryte outputs a colorful output by default using colorama, if colorama is installed.

The severity levels will be colored differently accordingly to the following mapping:

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

In an ideal world, when a user performs an action in an app, a context related to that event will be logged and attached to any log message relating to that event, so that it is possible to tail the entire flow from the moment the user performed the action and until, say, they got a response from the db.

This, unfortunately, is not provided in any log library I know of, and for a good reason - it depends on many factors potentially related to that specific app.

I would like to eventually provide a comfortable framework for many usecases, but for now, you can do something like the following:

```python
cid = wryter.event('User logging in', {'user_id': 'nir0s'})
# cid = {'cid': uuid.uuid4()}
wryter.debug('Requesting log-in host...', cid, ...)
...
wryter.debug('Querying db for available server...', cid, ...)
...
wryter.info('Host is: {0}'.format(host_ip))

...
```

The idea behind this is that a uuid is generated for each event and can then be passed into any log message within the same context. "within the same context" is a very abstract defintion, and is up to the developer to implement as it might be thread-related, framework-related, or else. I intend to expand the framework, but for now, that's what it is.

## Testing

```shell
git clone git@github.com:nir0s/wryte.git
cd wryte
pip install tox
tox
```
