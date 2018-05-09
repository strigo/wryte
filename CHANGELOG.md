## 0.3.0 (UNRELEASED)

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
