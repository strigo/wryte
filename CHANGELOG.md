## 2.0.0 (TBD)

BACKWARD COMPATIBILITY:
* Remove official Python 3.5 and 3.6 support

RELEASE:
* Test on Python v3.10
* Update classifiers
* Update relevant click version
* Upgrade dev requirements
* Remove unusued pytype


## 1.0.0 (2020.11.21)

BACKWARD COMPATIBILITY:
* Remove official Python 2.7 and 3.4 support [[ededefb](https://github.com/strigo/wryte/commit/ededefbf4d6e4667c2afdb73cb2be6c410e2e262)]
* Remove Elasticsearch, syslog and logz.io handlers [[14f0a10](https://github.com/strigo/wryte/commit/14f0a10d52df2f9e347a26407bc283869ef069e9)]
* Change the default env var that enables file logging to `HANDLERS_FILE_PATH` [[14f0a10](https://github.com/strigo/wryte/commit/14f0a10d52df2f9e347a26407bc283869ef069e9)]

ENHANCEMENTS:
* Blacken wryte.py [[7f44167](https://github.com/strigo/wryte/commit/7f4416736faffae2290518a30e2603139a8c4885)]

RELEASE:
* Optimize tox config and add black validation [[2793d7b](https://github.com/strigo/wryte/commit/2793d7bc9f7254aa9123ee4e99d7b6066ceec8e8)]
* Add pre-commit config [[df03781](https://github.com/strigo/wryte/commit/df037814e80058b7eb62194fb4f2cc8d088e124f)]
* Default to Python 3.7 when building and testing.

## 0.3.0 (2018.05.09)

ENHANCEMENTS:
* Add support for ec2 specific contextual fields [[#27](https://github.com/nir0s/wryte/issues/27)]
* Replace `datetime.now()` with `datetime.utcnow()` [[33e9c11](https://github.com/nir0s/wryte/commit/33e9c118a345d8edcf099dd330badf5912cbf21a)]
* Optimize performance (benchmarks will come soon) [[#26](https://github.com/nir0s/wryte/issues/26)]

BUG FIXES:
* Reinstate k=v pair string handling only for the CLI [[728a274](https://github.com/nir0s/wryte/commit/728a274326d290791ded54e41714065f3e7f9902)]


## 0.2.1 (2018.03.26)

This release includes many changes from different unofficial releases and is also the first official release
which I feel is ready for day to day use.

* Add colored human readable ConsoleFormatter, which is used with the default stream handler.
* Support pretty-printing key=value pairs.
* Add mucho documentation.
* Allow to remove and list handlers.
* Allow to pass custom formatter.
* Add a `log` method which receives a logging level, message and objects.
* Support colored console output.
* Add an `event` method which returns a `cid` (context id). The cid can also be passed into the event method via the `cid` flag.
* Add `bind` and `unbind` methods for binding context to a logger.
* Add `set_level` method for setting the logger's level.
* Support changing log level via the `_set_level` flag in `critical` and `error` log levels.
* Support printing a simple message without any formatting (only the `message` field and kv pairs are printed).
* Support passing kwarg type context to all logging methods (i.e. `wryter.error('Message', k=v)`.
* Add OOB support (with optional dependencies) for Elasticsearch, Logzio, Syslog and File handlers.
* Expose handler configuration via env vars.
* Add many tests
* Add codeclimate checks
* Try to avoid exceptions in the logger as much as possible. Instead, display errors or exceptions in the console.

See the docs for more info.


## 0.1.0 (2017.12.19)

* Initial implementation
* Make basic logger log a standard log message.
* Add a basic CLI for the development process and for user testing.
* Use Click for CLI which should be removed later to remove overhead.
* Support JSON output.
* Support Pretty Printing JSON.
* Allow to pass logger name
* Allow to pass logger level
* Allow to pass hostname
* Auto-add base fields to each JSON message: `hostname`, `name`, `pid`, `timestamp`, `level`.
