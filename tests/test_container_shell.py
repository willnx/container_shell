# -*- coding: UTF-8 -*-
"""A suite of unit tests for the container_shell module"""
import unittest
from unittest.mock import patch, MagicMock

import docker

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

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_kill_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                         fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell`` Ignores failures to kill a container because it's already been killed"""
        fake_get_config.return_value = (_default(), True, '')
        fake_container = MagicMock()
        fake_container.kill.side_effect = docker.errors.NotFound('Testing')
        fake_docker_client = MagicMock()
        fake_docker_client.containers.create.return_value = fake_container
        fake_docker_from_env.return_value = fake_docker_client

        container_shell.main()

        self.assertTrue(fake_container.kill.called)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_kill_unknown_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                                  fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell``  Logs unexpected errors when terminating/killing a container"""
        fake_get_config.return_value = (_default(), True, '')
        fake_logger = MagicMock()
        fake_get_logger.return_value = fake_logger
        fake_container = MagicMock()
        fake_container.kill.side_effect = Exception('Testing')
        fake_docker_client = MagicMock()
        fake_docker_client.containers.create.return_value = fake_container
        fake_docker_from_env.return_value = fake_docker_client

        container_shell.main()

        self.assertTrue(fake_logger.exception.called)



    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_remove_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                         fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell`` Ignores failures to delete a container because it's already been deleted"""
        fake_get_config.return_value = (_default(), True, '')
        fake_container = MagicMock()
        fake_container.remove.side_effect = docker.errors.NotFound('Testing')
        fake_docker_client = MagicMock()
        fake_docker_client.containers.create.return_value = fake_container
        fake_docker_from_env.return_value = fake_docker_client

        container_shell.main()

        self.assertTrue(fake_container.kill.called)

    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell.docker, 'from_env')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_remove_unknown_failure(self, fake_printerr, fake_dockage, fake_docker_from_env,
                                    fake_dockerpty, fake_get_config, fake_get_logger):
        """``container_shell`` Logs unexpected errors when deleting a container"""
        fake_get_config.return_value = (_default(), True, '')
        fake_logger = MagicMock()
        fake_get_logger.return_value = fake_logger
        fake_container = MagicMock()
        fake_container.remove.side_effect = Exception('Testing')
        fake_docker_client = MagicMock()
        fake_docker_client.containers.create.return_value = fake_container
        fake_docker_from_env.return_value = fake_docker_client

        container_shell.main()

        self.assertTrue(fake_logger.exception.called)



if __name__ == '__main__':
    unittest.main()
