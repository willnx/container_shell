# -*- coding: UTF-8 -*-
"""A suite of unit tests for the container_shell module"""
import argparse
import unittest
from unittest.mock import patch, MagicMock

import docker
import requests

from container_shell import container_shell
from container_shell.lib.config import _default


class TestContainerShellMain(unittest.TestCase):
    """A suite of test cases for the container_shell main function"""

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_basic(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                   fake_get_config, fake_get_logger):
        """``container_shell`` The 'main' function is runnable"""
        fake_get_config.return_value = (_default(), True, '')
        try:
            container_shell.main(cli_args=[])
        except Exception as doh:
            runable = False
        else:
            runable = True

        self.assertTrue(runable)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.subprocess, 'Popen')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'getpwnam')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_admin(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                   fake_get_config, fake_getpwnam, fake_exit, fake_Popen, fake_get_logger):
        """``conatiner_shell`` Skips invoking a container if the identity is white-listed"""
        fake_config = _default()
        fake_config['config']['skip_users'] = 'admin,bob,liz'
        fake_get_config.return_value = (fake_config, True, '')
        fake_user_info = MagicMock()
        fake_user_info.pw_name = 'admin'
        fake_user_info.pw_uid = 1000
        fake_getpwnam.return_value = fake_user_info

        container_shell.main(cli_args=[])

        self.assertTrue(fake_Popen.called)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_update_failure(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                            fake_get_config, fake_exit, fake_get_logger):
        """``container_shell`` Prints an error and exits if unable to update the container image"""
        fake_docker.errors.DockerException = Exception # Hack because I mock all of the `docker` lib
        fake_get_config.return_value = (_default(), True, '')
        fake_docker_client = MagicMock()
        fake_docker_client.images.pull.side_effect = docker.errors.DockerException('testing')
        fake_docker.from_env.return_value = fake_docker_client

        container_shell.main(cli_args=[])

        the_args, _  = fake_printerr.call_args
        error_msg = the_args[0]
        expected_msg = 'Unable to update login environment'

        self.assertEqual(error_msg, expected_msg)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_create_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                            fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell`` Generates an error message and bails if unable to create the container"""
        fake_get_config.return_value = (_default(), True, '')
        fake_docker_client = MagicMock()
        fake_docker_from_env.return_value = fake_docker_client
        fake_docker_client.containers.create.side_effect = docker.errors.DockerException('testing')
        try:
            container_shell.main(cli_args=[])
        except SystemExit:
            pass

        the_args, _  = fake_printerr.call_args
        error_msg = the_args[0]
        expected_msg = 'Failed to create login environment'

        self.assertEqual(error_msg, expected_msg)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_pty_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                         fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell`` Generates and error and bails if unable to connect to the container"""
        fake_get_config.return_value = (_default(), True, '')
        fake_dockerpty.start.side_effect = Exception('testing')
        try:
            container_shell.main(cli_args=[])
        except SystemExit:
            pass

        the_args, _ = fake_printerr.call_args
        error_msg = the_args[0]
        expected_msg = 'Failed to connect to PTY'

        self.assertEqual(error_msg, expected_msg)

    def test_kill_container(self):
        """``container_shell`` 'kill_container' only logs if there's an unexpected error"""
        fake_container = MagicMock()
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        # If you call hasattr() on MagicMock, it'll add the addr, but dir() doesn't
        attrs = dir(fake_logger)
        self.assertFalse(fake_logger.called)
        self.assertFalse('exception' in attrs)
        self.assertFalse('error' in attrs)
        self.assertFalse('info' in attrs)

    def test_kill_container_exec_run_error_ignore(self):
        """``container_shell`` 'kill_container' ignore errors if the container is already stopped"""
        fake_container = MagicMock()
        fake_resp = MagicMock()
        fake_resp.status_code = 409
        fake_container.exec_run.side_effect = [requests.exceptions.HTTPError('testing', response=fake_resp)]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        # If you call hasattr() on MagicMock, it'll add the addr, but dir() doesn't
        attrs = dir(fake_logger)
        self.assertFalse(fake_logger.called)
        self.assertFalse('exception' in attrs)
        self.assertFalse('error' in attrs)
        self.assertFalse('info' in attrs)

    def test_kill_container_exec_run_error(self):
        """``container_shell`` 'kill_container' logs unexpected errors when executing 'kill' in the container"""
        fake_container = MagicMock()
        fake_resp = MagicMock()
        fake_resp.status_code = 500
        fake_container.exec_run.side_effect = [requests.exceptions.HTTPError('testing', response=fake_resp)]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        self.assertTrue(fake_logger.exception.called)

    def test_kill_container_kill_ignore_404(self):
        """``container_shell`` 'kill_container' ignore expected errors when killing the container"""
        fake_container = MagicMock()
        fake_resp = MagicMock()
        fake_resp.status_code = 404
        fake_container.kill.side_effect = [requests.exceptions.HTTPError('testing', response=fake_resp)]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        # If you call hasattr() on MagicMock, it'll add the addr, but dir() doesn't
        attrs = dir(fake_logger)
        self.assertFalse(fake_logger.called)
        self.assertFalse('exception' in attrs)
        self.assertFalse('error' in attrs)
        self.assertFalse('info' in attrs)

    def test_kill_container_kill_ignore_409(self):
        """``container_shell`` 'kill_container' ignore expected errors when killing the container"""
        fake_container = MagicMock()
        fake_resp = MagicMock()
        fake_resp.status_code = 409
        fake_container.kill.side_effect = [requests.exceptions.HTTPError('testing', response=fake_resp)]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        # If you call hasattr() on MagicMock, it'll add the addr, but dir() doesn't
        attrs = dir(fake_logger)
        self.assertFalse(fake_logger.called)
        self.assertFalse('exception' in attrs)
        self.assertFalse('error' in attrs)
        self.assertFalse('info' in attrs)

    def test_kill_container_kill_logs(self):
        """``container_shell`` 'kill_container' logs unexpected errors when killing the container"""
        fake_container = MagicMock()
        fake_resp = MagicMock()
        fake_resp.status_code = 500
        fake_container.kill.side_effect = [requests.exceptions.HTTPError('testing', response=fake_resp)]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        self.assertTrue(fake_logger.exception.called)

    def test_kill_container_kill_exception(self):
        """``container_shell`` 'kill_container' logs generic exception errors when killing the container"""
        fake_container = MagicMock()
        fake_container.kill.side_effect = [RuntimeError('testing')]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        self.assertTrue(fake_logger.exception.called)

    def test_remove_not_found(self):
        """``container_shell`` 'kill_container' ignores errors when trying to delete an already deleted container"""
        fake_container = MagicMock()
        fake_container.remove.side_effect = [docker.errors.NotFound('testing')]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        # If you call hasattr() on MagicMock, it'll add the addr, but dir() doesn't
        attrs = dir(fake_logger)
        self.assertFalse(fake_logger.called)
        self.assertFalse('exception' in attrs)
        self.assertFalse('error' in attrs)
        self.assertFalse('info' in attrs)

    def test_remove_exception(self):
        """``container_shell`` 'kill_container' logs unexpected errors when trying to delete a container"""
        fake_container = MagicMock()
        fake_container.remove.side_effect = [RuntimeError('testing')]
        the_signal = 'SIGHUP'
        fake_logger = MagicMock()

        container_shell.kill_container(fake_container, the_signal, fake_logger)
        self.assertTrue(fake_logger.exception.called)

    @patch.object(container_shell.signal, 'signal')
    def test_set_signal_handlers(self, fake_signal):
        """``container_shell`` 'set_signal_handlers' sets the expected signal handlers"""
        fake_container = MagicMock()
        fake_logger = MagicMock()

        container_shell.set_signal_handlers(fake_container, fake_logger)
        signals_handled = [x[0][0].name for x in fake_signal.call_args_list]
        expected = ['SIGHUP', 'SIGINT', 'SIGQUIT', 'SIGABRT', 'SIGTERM']

        # set() avoids false positive due to difference in ordering
        self.assertEqual(set(signals_handled), set(expected))
        self.assertTrue(len(signals_handled) == 5)

    def test_parse_cli(self):
        """``container_shell`` 'parse_cli' returns a Namespace object"""
        fake_args = []
        args = container_shell.parse_cli(fake_args)

        self.assertTrue(isinstance(args, argparse.Namespace))

    def test_parse_cli_command_arg(self):
        """``container_shell`` 'parse_cli' supports the '--command' argument"""
        fake_args = ['--command', 'some command']
        args = container_shell.parse_cli(fake_args)

        expected = 'some command'
        actual = args.command

        self.assertEqual(expected, actual)

    def test_parse_cli_c_arg(self):
        """``container_shell`` 'parse_cli' supports the '-c' argument"""
        fake_args = ['-c', 'some command']
        args = container_shell.parse_cli(fake_args)

        expected = 'some command'
        actual = args.command

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
