Pen
===

[![Travis Build Status](https://travis-ci.org/nir0s/pen.svg?branch=master)](https://travis-ci.org/nir0s/pen)
[![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/kuf0x8j62kts1bpg/branch/master?svg=true)](https://ci.appveyor.com/project/nir0s/pen)
[![PyPI Version](http://img.shields.io/pypi/v/ghost.svg)](http://img.shields.io/pypi/v/ghost.svg)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/ghost.svg)](https://img.shields.io/pypi/pyversions/ghost.svg)
[![Requirements Status](https://requires.io/github/nir0s/pen/requirements.svg?branch=master)](https://requires.io/github/nir0s/pen/requirements/?branch=master)
[![Code Coverage](https://codecov.io/github/nir0s/pen/coverage.svg?branch=master)](https://codecov.io/github/nir0s/pen?branch=master)
[![Code Quality](https://landscape.io/github/nir0s/pen/master/landscape.svg?style=flat)](https://landscape.io/github/nir0s/pen)
[![Is Wheel](https://img.shields.io/pypi/wheel/ghost.svg?style=flat)](https://pypi.python.org/pypi/ghost)


Pen aims to provide a very simple API for logging simple log messages and JSON objects in Python.


Example:

```python
import pen

pen.info('My Message', {'key=value'}, 'who=where')
2017-12-19 15:16:46,767 - TEST - INFO - My Message {"key": "value"} {"who": "where"}
...

```

```python
from pen import Pen

pen = Pen(name='my_logger', jsonify=True, pretty=False, level='info')
pen.warn('TEST_MESSAGE', {'key': 'value'}, 'who=where')
{"hostname": "nir0s-x1", "pid": 23102, "timestamp": "2017-12-19T15:21:32.562337", "message": "TEST_MESSAGE", "who": "where", "level": "warning", "key": "value", "name": "my_logger"}
...

```


## Alternatives

...

## Installation

Pen supports Linux, Windows and OSX on Python 2.7 and 3.4+

```shell
pip install pen
```

For dev:

```shell
pip install https://github.com/nir0s/pen/archive/master.tar.gz
```

## Testing

```shell
git clone git@github.com:nir0s/pen.git
cd ghost
pip install tox
tox
```
