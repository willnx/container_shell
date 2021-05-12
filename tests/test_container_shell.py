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

    @patch.object(container_shell, '_block_on_init')
    @patch.object(container_shell.atexit, 'register')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_basic(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                   fake_get_config, fake_get_logger, fake_register, fake_block_on_init):
        """``container_shell`` The 'main' function is runnable"""
        fake_get_config.return_value = (_default(), True, '')
        try:
            container_shell.main(cli_args=[])
        except Exception as doh:
            runable = False
        else:
            runable = True

        self.assertTrue(runable)

    @patch.object(container_shell, '_block_on_init')
    @patch.object(container_shell.atexit, 'register')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_custom_config(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                   fake_get_config, fake_get_logger, fake_register, fake_block_on_init):
        """``container_shell`` Logs custom configs at DEBUG level"""
        fake_logger = MagicMock()
        fake_get_logger.return_value = fake_logger
        fake_get_config.return_value = (_default(), False, '')

        try:
            container_shell.main(cli_args=[])
        except Exception as doh:
            ok = False
        else:
            ok = fake_logger.debug.called

        self.assertTrue(ok)

    @patch.object(container_shell, '_block_on_init')
    @patch.object(container_shell.atexit, 'register')
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
                   fake_get_config, fake_getpwnam, fake_exit, fake_Popen, fake_get_logger,
                   fake_register, fake_block_on_init):
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


    @patch.object(container_shell, '_block_on_init')
    @patch.object(container_shell.atexit, 'register')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_update_failure(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                            fake_get_config, fake_exit, fake_get_logger, fake_register, fake_block_on_init):
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

    @patch.object(container_shell, '_get_container')
    @patch.object(container_shell.atexit, 'register')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_get_container_failure(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                                   fake_get_config, fake_exit, fake_get_logger, fake_register,
                                   fake_get_container):
        """``container_shell`` Prints an error if unable to obtain a container"""
        fake_docker.errors.DockerException = Exception
        fake_get_config.return_value = (_default(), True, '')
        fake_get_container.side_effect = docker.errors.DockerException('testing')

        container_shell.main(cli_args=[])

        the_args, _ = fake_printerr.call_args_list
        error_msg = the_args[0][0]
        expected_msg = 'Failed to create login environment'

        self.assertEqual(error_msg, expected_msg)

    @patch.object(container_shell, '_get_container')
    @patch.object(container_shell.atexit, 'register')
    @patch.object(container_shell.utils, 'get_logger')
    @patch.object(container_shell.sys, 'exit')
    @patch.object(container_shell, 'get_config')
    @patch.object(container_shell, 'dockerpty')
    @patch.object(container_shell, 'docker')
    @patch.object(container_shell, 'dockage')
    @patch.object(container_shell.utils, 'printerr')
    def test_get_container_standalone(self, fake_printerr, fake_dockage, fake_docker, fake_dockerpty,
                                      fake_get_config, fake_exit, fake_get_logger, fake_register,
                                      fake_get_container):
        """``container_shell`` Runs dockerpty.start for standalone containers"""
        fake_get_config.return_value = (_default(), True, '')
        fake_get_container.return_value = MagicMock(), True

        container_shell.main(cli_args=[])


        self.assertTrue(fake_dockerpty.start.called)


class TestGetContainer(unittest.TestCase):
    """A suite of test cases for the ``_get_container`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.config = _default()
        cls.docker_client = MagicMock()
        cls.create_kwargs = {}

    def test_shared_env(self):
        """``container_shell`` '_get_container' locates and returns an existing container for shared environments"""
        existing_container = MagicMock()
        existing_container.name = 'pat'
        containers = [MagicMock(), existing_container, MagicMock()]
        self.docker_client.containers.list.return_value = containers

        found, stanalone = container_shell._get_container(self.docker_client,
                                                  'pat',
                                                  self.config,
                                                  **self.create_kwargs)

        self.assertTrue(found is existing_container)
        self.assertFalse(stanalone)

    @patch.object(container_shell, '_block_on_init')
    def test_creates(self, fake_block_on_init):
        """``container_shell`` '_get_container' makes a container for shared environment is none exist already"""
        containers = [MagicMock(), MagicMock()]
        self.docker_client.containers.list.return_value = containers
        new_container = MagicMock()
        new_container.status = 'created'
        self.docker_client.containers.create.return_value = new_container

        found, _ = container_shell._get_container(self.docker_client,
                                                 'joe',
                                                 self.config,
                                                 **self.create_kwargs)

        self.assertTrue(found is new_container)
        self.assertTrue(self.docker_client.containers.create.called)
        self.assertTrue(found.start.called)

    def test_standalone(self):
        """``container_shell`` '_get_container' creates a new container for SCP commands"""
        # "-f" is a hidden flag, and how scp sends a file from a local machine to yours over SSH.
        self.config['config']['command'] = 'scp -f /tmp/test.txt'

        containers = [MagicMock(), MagicMock()]
        self.docker_client.containers.list.return_value = containers
        new_container = MagicMock()
        self.docker_client.containers.create.return_value = new_container

        found, stanalone = container_shell._get_container(self.docker_client,
                                                 'joe',
                                                 self.config,
                                                 **self.create_kwargs)

        self.assertTrue(found is new_container)
        self.assertTrue(stanalone)
        self.assertTrue(self.docker_client.containers.create.called)

    def test_standalone_not_started(self):
        """``container_shell`` '_get_container' standalone containers are not started"""
        # "-t" is a hidden flag, and how scp accepts a file from your on the remove machine over SSH.
        self.config['config']['command'] = 'scp -t /tmp/test.txt'

        containers = [MagicMock(), MagicMock()]
        self.docker_client.containers.list.return_value = containers
        new_container = MagicMock()
        self.docker_client.containers.create.return_value = new_container

        found, _ = container_shell._get_container(self.docker_client,
                                                 'joe',
                                                 self.config,
                                                 **self.create_kwargs)

        self.assertFalse(found.start.called)

    @patch.object(container_shell.time, 'sleep')
    def test_block_on_init(self, fake_sleep):
        """``container_shell`` '_block_on_init' waits until the user is created in the container"""
        fake_container = MagicMock()
        fake_exec = MagicMock()
        fake_exec.exit_code = 0
        fake_container.exec_run.side_effect = [MagicMock(), fake_exec]

        container_shell._block_on_init(fake_container, 'sally', '/usr/bin/id')

        self.assertTrue(fake_sleep.called)

    @patch.object(container_shell.time, 'time')
    @patch.object(container_shell.time, 'sleep')
    def test_block_on_init_timeout(self, fake_sleep, fake_time):
        """``container_shell`` '_block_on_init' raises RuntimeError upon timeout"""
        fake_container = MagicMock()
        fake_time.side_effect = [1, 9001]

        with self.assertRaises(RuntimeError):
            container_shell._block_on_init(fake_container, 'sally', '/usr/bin/id')


class TestShouldNotKill(unittest.TestCase):
    """A suite of test cases for the ``_should_not_kill`` function"""
    @classmethod
    def setUp(cls):
        """Runs before each test case"""
        cls.container = MagicMock()
        cls.ps_output = b'some output'
        cls.container.exec_run.return_value = ('', cls.ps_output)
        cls.container.attrs = {'ExecIDs' : None}
        cls.logger = MagicMock()
        cls.persist = 'true'
        cls.persist_egrep = 'tmux|screen|coreutils'
        cls.ps_path = '/bin/ps'

    def test_should_not_kill(self):
        """``container_shell`` '_should_not_kill' returns False if no running execs, persist is false, and no background jobs are found"""
        answer = container_shell._should_not_kill(self.container,
                                                  self.persist,
                                                  self.persist_egrep,
                                                  self.ps_path,
                                                  self.logger)
        self.assertFalse(answer)

    def test_should_not_kill_execs(self):
        """``container_shell`` '_should_not_kill' returns True if execs are running against the container"""
        self.container.attrs['ExecIDs'] = [MagicMock(), MagicMock()]
        answer = container_shell._should_not_kill(self.container,
                                                  self.persist,
                                                  self.persist_egrep,
                                                  self.ps_path,
                                                  self.logger)
        self.assertTrue(answer)

    def test_should_not_kill_no_persist(self):
        """``container_shell`` '_should_not_kill' returns False if no running execs and persist is false"""
        self.persist = 'false'
        answer = container_shell._should_not_kill(self.container,
                                                  self.persist,
                                                  self.persist_egrep,
                                                  self.ps_path,
                                                  self.logger)
        self.assertFalse(answer)

    def test_should_not_kill_background_jobs(self):
        """``container_shell`` '_should_not_kill' returns True if persist is true and background jobs are found"""
        ps_output = b'USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nsally\t20\t0.0\t.0.0\t0\t0\t?\tS\tFed08\t0:00\t screen'
        self.container.exec_run.return_value = ('', ps_output)
        answer = container_shell._should_not_kill(self.container,
                                                  self.persist,
                                                  self.persist_egrep,
                                                  self.ps_path,
                                                  self.logger)

        self.assertTrue(answer)

    def test_container_not_found(self):
        """``container_shell`` '_should_not_kill' returns None if the container doesn't exist"""
        docker.errors.NotFound = Exception
        self.container.exec_run.side_effect = Exception('Testing')

        answer = container_shell._should_not_kill(self.container,
                                                  self.persist,
                                                  self.persist_egrep,
                                                  self.ps_path,
                                                  self.logger)

        self.assertTrue(answer is None)


class TestKillContainer(unittest.TestCase):
    """A suite of test cases for the ``kill_container`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.container = MagicMock()
        cls.logger = MagicMock()
        cls.persist = 'false'
        cls.persist_egrep = 'tmux|screen|coreutils'
        cls.ps_path = '/bin/ps'
        cls.the_signal = 'SIGTERM'
        cls.container.attrs = {'ExecIDs' : None}
        cls.container.exec_run.return_value = ('', b'some output')

    def test_kill_container(self):
        """``container_shell`` 'kill_container' sends the supplied signal to PID 1"""
        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        the_args, _ = self.container.exec_run.call_args
        kill_cmd = the_args[0]
        expected = 'kill -SIGTERM 1'

        self.assertEqual(kill_cmd, expected)

    def test_kill_container_should_not(self):
        """``container_shell`` 'kill_container' bails early if it should_not_kill"""
        self.container.attrs['ExecIDs'] = [MagicMock()]
        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertEqual(self.logger.debug.call_count, 0)

    @patch.object(container_shell, '_should_not_kill')
    def test_kill_ignores_404(self, fake_should_not_kill):
        """``container_shell`` 'kill_container' ignores failures to kill a container that's not found"""
        fake_should_not_kill.return_value = False
        fake_resp = MagicMock()
        fake_resp.status_code = 404
        error = docker.errors.APIError("NOT FOUND", response=fake_resp)
        self.container.exec_run.side_effect = error

        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertFalse(self.logger.exception.called)

    @patch.object(container_shell, '_should_not_kill')
    def test_kill_ignores_409(self, fake_should_not_kill):
        """``container_shell`` 'kill_container' ignores failures to kill a container that's not running"""
        fake_should_not_kill.return_value = False
        fake_resp = MagicMock()
        fake_resp.status_code = 409
        error = docker.errors.APIError("CONFLICT", response=fake_resp)
        self.container.exec_run.side_effect = error

        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertFalse(self.logger.exception.called)


    @patch.object(container_shell, '_should_not_kill')
    def test_kill_logs_unexpected(self, fake_should_not_kill):
        """``container_shell`` 'kill_container' logs unexpected erros when trying to kill a container"""
        fake_should_not_kill.return_value = False
        fake_resp = MagicMock()
        fake_resp.status_code = 500
        error = docker.errors.APIError("SERVER ERROR", response=fake_resp)
        self.container.exec_run.side_effect = error

        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertTrue(self.logger.exception.called)

    def test_kill_container_remove(self):
        """``container_shell`` 'kill_container' removes containers it's killed"""
        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertTrue(self.container.remove.called)

    def test_kill_container_remove_gone(self):
        """``container_shell`` 'kill_container' ignores failures to remove containers that no longer exist"""
        self.container.remove.side_effect = docker.errors.NotFound("testing")
        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertFalse(self.logger.exception.called)

    def test_kill_container_remove_error(self):
        """``container_shell`` 'kill_container' logs unexpected failures to remove containers"""
        self.container.remove.side_effect = Exception("testing")
        container_shell.kill_container(self.container,
                                       self.the_signal,
                                       self.persist,
                                       self.persist_egrep,
                                       self.ps_path,
                                       self.logger)

        self.assertTrue(self.logger.exception.called)


class TestParseCli(unittest.TestCase):
    """A suite of test cases for the ``parse_cli`` function"""

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
