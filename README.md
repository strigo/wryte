Wryte
=====

[![Travis Build Status](https://travis-ci.org/nir0s/wryte.svg?branch=master)](https://travis-ci.org/nir0s/wryte)
[![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/kuf0x8j62kts1bpg/branch/master?svg=true)](https://ci.appveyor.com/project/nir0s/wryte)
[![PyPI Version](http://img.shields.io/pypi/v/ghost.svg)](http://img.shields.io/pypi/v/ghost.svg)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/ghost.svg)](https://img.shields.io/pypi/pyversions/ghost.svg)
[![Requirements Status](https://requires.io/github/nir0s/wryte/requirements.svg?branch=master)](https://requires.io/github/nir0s/wryte/requirements/?branch=master)
[![Code Coverage](https://codecov.io/github/nir0s/wryte/coverage.svg?branch=master)](https://codecov.io/github/nir0s/wryte?branch=master)
[![Code Quality](https://landscape.io/github/nir0s/wryte/master/landscape.svg?style=flat)](https://landscape.io/github/nir0s/wryte)
[![Is Wheel](https://img.shields.io/pypi/wheel/ghost.svg?style=flat)](https://pypi.python.org/pypi/ghost)


NOTE: WIP!


Wryte aims to provide a simple API for logging in Python for both simple and JSON based messages.

## Design principles:

* Formatter and Handler agnostic - you will be able to pass whichever formats and handlers you desire.
* While also providing default implementations for the most common handlers.
* Enrich with basic metadata (e.g. hostname, pid, etc..)
* Support both human readable and machine readable strings for console output and server aggregation.
* Single transportable module with (by default) no non-stdlib dependencies.


https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
https://www.loggly.com/ultimate-guide/python-logging-basics/
https://github.com/trentm/node-bunyan

Example:

```python
from wryte import Wryte

# timestamp, name, level, message

pen = Wryte(name='app')
pen.info('My Message')
2017-12-22T17:02:59.550920 - app - INFO - my message

pen.info('My Message', {'key1': 'value2', 'key2': 'value2'}, 'who=where')
2017-12-22T17:02:59.550920 - app - INFO - my message
  key1=value1,
  key2=value2,
  who=where

...
pen = Wryte(name='wryte', pretty=True, level='debug', base=True, jsonify=True)
pen.debug('TEST_MESSAGE', {'w00t': 'what'}, 'who=where')
{
    "hostname": "nir0s-x1",
    "level": "warning",
    "message": "TEST_MESSAGE",
    "pid": 8554,
    "who": "where",
    "name": "wryte",
    "w00t": "what",
    "timestamp": "2017-12-22T14:19:09.828625"
}



```
<!--
```python
from wryte import Wryte

pencil = Wryte(name='my_logger', jsonify=True, pretty=False, level='info', enrich=True)
pencil.warn('TEST_MESSAGE', {'key': 'value'}, 'who=where')
...

``` -->


## Alternatives

...

## Installation

Pen supports Linux, Windows and OSX on Python 2.7 and 3.4+

```shell
pip install pen
```

For dev:

```shell
pip install https://github.com/nir0s/wryte/archive/master.tar.gz
```

## Testing

```shell
git clone git@github.com:nir0s/wryte.git
cd ghost
pip install tox
tox
```
