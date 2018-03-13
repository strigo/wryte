import sys
import uuid
import shlex
import logging

import mock
import pytest
import click.testing as clicktest

import wryte
from wryte import Wryte


def _invoke(command):
    cli = clicktest.CliRunner()

    lexed_command = command if isinstance(command, list) \
        else shlex.split(command)
    func = lexed_command[0]
    params = lexed_command[1:]
    return cli.invoke(getattr(wryte, func), params)


class TestWryte(object):
    def test_simple(self):
        w = Wryte(name=str(uuid.uuid4()), simple=True)
        w.info('My Message')
        w.event('My Event')
        w.debug('My Message', {'k': 'v'})

    def test_json(self):
        w = Wryte(name=str(uuid.uuid4()), jsonify=True)
        w.info('My Message')

    def test_ugly(self):
        w = Wryte(name=str(uuid.uuid4()), pretty=False)
        w.info('My Message', k='v')

    def test_no_color(self):
        w = Wryte(name=str(uuid.uuid4()), color=False)
        w.info('My Message')

    def test_context_type(self):
        """Test the different types of context

        * Dicts
        * Nested dicts
        * JSON strings
        * kwargs
        * kv strings
        * bad object
        """
        w = Wryte(name=str(uuid.uuid4()))
        w.info('Message 1', k1='v1', k2='v2')
        w.info('Message 2', {'k1': 'v1', 'k2': 'v2'})
        w.info('Message 3', '{"k1": "v1", "k2": "v2"}')
        w.info('Message 4', {'k1': 'v1', 'k2': {'k3': 'v3'}})
        w.info(
            'Message 5',
            {'k3': 'v3', 'k4': 'v4'},
            {'k7': 'v7', 'k8': {'k9': 'v9'}},
            '{"k5": "v5", "k6": "v6"}',
            'bla',
            k1='v1', k2='v2',
        )

    def test_logging_levels(self):
        w = Wryte(name=str(uuid.uuid4()))

        w.event('Event')
        w.log('info', 'My Message')
        w.debug('Debug Message')
        w.info('Info Message')
        w.warning('Warning Message')
        w.warn('Warning Message')
        w.error('Error Message')
        w.critical('Critical Message')

    def test_event(self):
        w = Wryte(name=str(uuid.uuid4()))

        cid = w.event('Event', cid='user_id')
        assert cid == 'user_id'

        cid = w.event('Event')
        assert len(cid) == len(str(uuid.uuid4()))

    def test_bind_unbind(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert 'k' not in w._log.keys()
        w.bind({'k1': 'v1'}, '{"k2": "v2"}', k3='v3')
        assert 'k1' in w._log.keys()
        assert 'k2' in w._log.keys()
        assert 'k3' in w._log.keys()
        w.unbind('k1', 'k2', 'k3')
        assert 'k1' not in w._log.keys()
        assert 'k2' not in w._log.keys()
        assert 'k3' not in w._log.keys()

    def test_bare_handler(self):
        w = Wryte(name=str(uuid.uuid4()), bare=True)
        assert len(w.list_handlers()) == 0

    def test_add_handler(self):
        w = Wryte(name=str(uuid.uuid4()), bare=True)
        assert len(w.list_handlers()) == 0

        name = w.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter='json',
            level='debug')

        assert len(w.list_handlers()) == 1
        assert w.list_handlers() == ['_json']
        assert name == '_json'
        assert w.logger.getEffectiveLevel() == 10

    def test_add_handler_bad_level(self):
        w = Wryte(name=str(uuid.uuid4()), bare=True)
        w.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter='json',
            level='BOOBOO')
        assert len(w.list_handlers()) == 0

    def test_another_formatter(self):
        w = Wryte(name=str(uuid.uuid4()), bare=True)
        w.add_handler(
            handler=logging.StreamHandler(sys.stdout),
            name='_json',
            formatter=wryte.ConsoleFormatter(),
            level='info')

    def test_list_handlers(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert len(w.list_handlers()) == 1
        assert w.list_handlers() == ['_console']

    def test_list_handlers_no_handlers_configured(self):
        w = Wryte(name=str(uuid.uuid4()), bare=True)
        assert len(w.list_handlers()) == 0
        assert w.list_handlers() == []

    def test_remove_handler(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert len(w.list_handlers()) == 1
        assert w.list_handlers() == ['_console']

        w.remove_handler('_console')
        assert len(w.list_handlers()) == 0
        assert w.list_handlers() == []

    def test_remove_nonexisting_handler(self):
        w = Wryte(name=str(uuid.uuid4()))
        w.remove_handler('banana')
        assert len(w.list_handlers()) == 1

    def test_set_level(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert w.logger.getEffectiveLevel() == 20
        w.set_level('debug')
        assert w.logger.getEffectiveLevel() == 10

    def test_set_bad_level(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert w.logger.getEffectiveLevel() == 20
        w.set_level('deboog')
        assert w.logger.getEffectiveLevel() == 20

    def test_log_bad_level(self):
        w = Wryte(name=str(uuid.uuid4()))
        w.log('booboo', 'My Error')

    def test_set_level_from_error(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert w.logger.getEffectiveLevel() == 20
        w.error('My Error', _set_level='debug')
        assert w.logger.getEffectiveLevel() == 10

    def test_set_level_from_critical(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert w.logger.getEffectiveLevel() == 20
        w.critical('My Error', _set_level='debug')
        assert w.logger.getEffectiveLevel() == 10

    def test_set_level_from_log(self):
        w = Wryte(name=str(uuid.uuid4()))
        assert w.logger.getEffectiveLevel() == 20
        w.log('error', 'My Error', _set_level='debug')
        assert w.logger.getEffectiveLevel() == 10

    def test_cli(self):
        _invoke('main info My Message x=y')
