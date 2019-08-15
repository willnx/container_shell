# -*- coding: UTF-8 -*-
"""A suite of unit tests for the container_shell module"""
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
            container_shell.main()
        except Exception:
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

        container_shell.main()

        self.assertTrue(fake_Popen.called)

    @patch.object(container_shell.os, 'getenv')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.subprocess, 'call')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'getpwnam')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_scp(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                 fake_get_config, fake_getpwnam, fake_exit, fake_call, fake_get_logger,
                 fake_getenv):
        """``conatiner_shell`` Skips invoking a container if the identity is white-listed"""
        fake_config = _default()
        fake_getenv.return_value = 'scp -v -t /some/file.txt'
        fake_get_config.return_value = (fake_config, True, '')
        fake_user_info = MagicMock()
        fake_user_info.pw_name = 'admin'
        fake_user_info.pw_uid = 1000
        fake_getpwnam.return_value = fake_user_info

        container_shell.main()

        self.assertTrue(fake_call.called)

    @patch.object(container_shell.os, 'getenv')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.subprocess, 'call')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'getpwnam')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_scp_disabled(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                          fake_get_config, fake_getpwnam, fake_exit, fake_call, fake_get_logger,
                          fake_getenv):
        """``conatiner_shell`` Skips invoking a container if the identity is white-listed"""
        fake_config = _default()
        fake_config['config']['disable_scp'] = 'true'
        fake_getenv.return_value = 'scp -v -t /some/file.txt'
        fake_get_config.return_value = (fake_config, True, '')
        fake_user_info = MagicMock()
        fake_user_info.pw_name = 'admin'
        fake_user_info.pw_uid = 1000
        fake_getpwnam.return_value = fake_user_info

        container_shell.main()

        self.assertFalse(fake_call.called)

    @patch.object(container_shell.os, 'getenv')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.subprocess, 'call')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'getpwnam')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_sftp(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                  fake_get_config, fake_getpwnam, fake_exit, fake_call, fake_get_logger,
                  fake_getenv):
        """``conatiner_shell`` Skips invoking a container if SCP is enabled and SFTP is being used"""
        fake_config = _default()
        fake_getenv.return_value = '/some/path/to/sftp-server'
        fake_get_config.return_value = (fake_config, True, '')
        fake_user_info = MagicMock()
        fake_user_info.pw_name = 'admin'
        fake_user_info.pw_uid = 1000
        fake_getpwnam.return_value = fake_user_info

        container_shell.main()

        self.assertTrue(fake_call.called)

    @patch.object(container_shell.os, 'getenv')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.subprocess, 'call')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'getpwnam')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_sftp_disabled(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                           fake_get_config, fake_getpwnam, fake_exit, fake_call, fake_get_logger,
                           fake_getenv):
        """``conatiner_shell`` Denies use of SFTP if SCP is disabled"""
        fake_config = _default()
        fake_config['config']['disable_scp'] = 'true'
        fake_getenv.return_value = '/some/path/to/sftp-server'
        fake_get_config.return_value = (fake_config, True, '')
        fake_user_info = MagicMock()
        fake_user_info.pw_name = 'admin'
        fake_user_info.pw_uid = 1000
        fake_getpwnam.return_value = fake_user_info

        container_shell.main()

        self.assertFalse(fake_call.called)

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

        container_shell.main()

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
            container_shell.main()
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
            container_shell.main()
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


if __name__ == '__main__':
    unittest.main()
