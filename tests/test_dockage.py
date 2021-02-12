# -*- coding: UTF-8 -*-
"""A suite of unit tests for the ``dockage.py`` module"""
import unittest
from unittest.mock import patch, MagicMock

import docker

from container_shell.lib import dockage
from container_shell.lib.config import _default


class TestBuildArgs(unittest.TestCase):
    """A suite of unit tests for the ``build_args`` wrapper"""
    @patch.object(dockage, 'generate_name')
    @patch.object(dockage, 'container_command')
    @patch.object(dockage, 'mounts')
    @patch.object(dockage, 'dns')
    @patch.object(dockage, 'qos')
    def test_basic(self, fake_qos, fake_dns, fake_mounts, fake_container_command,
                   fake_generate_name):
        """``dockage`` 'build_args' is a simple wrapper"""
        config = _default()
        username = 'martin'
        user_uid = 9001
        user_gid = 9001
        logger = MagicMock()

        dockage.build_args(config, username, user_uid, user_gid, logger)

        self.assertTrue(fake_qos.called)
        self.assertTrue(fake_dns.called)
        self.assertTrue(fake_mounts.called)
        self.assertTrue(fake_container_command.called)
        self.assertTrue(fake_generate_name.called)


class TestDns(unittest.TestCase):
    """A suite of test cases for the ``dns`` function"""
    def test_no_addrs(self):
        """``dockage`` 'dns' returns None if no DNS server IPs are supplied"""
        output = dockage.dns(addrs='')

        self.assertTrue(output is None)

    def test_has_addrs(self):
        """``dockage`` 'dns' returns a list of DNS server IPs when provided with addresses"""
        output = dockage.dns(addrs='8.8.8.8,8.8.8.9')
        expected = ['8.8.8.8', '8.8.8.9']

        self.assertEqual(output, expected)

    def test_cleans_addrs(self):
        """``dockage`` 'dns' does it's best to clean up the IPs"""
        output = dockage.dns(addrs='1.2.3.4 ,\n4.5.6.7')
        expected = ['1.2.3.4', '4.5.6.7']

        self.assertEqual(output, expected)


class TestMounts(unittest.TestCase):
    """A suite of test cases for the ``mounts`` function"""
    def test_objects(self):
        """``dockage`` 'mounts' returns a list of docker.types.Mount objects"""
        mount_dict = {'/home' : '/home'}

        mount_obj = dockage.mounts(mount_dict)[0]
        expected = docker.types.Mount(source='/home', target='/home', type='bind')

        self.assertEqual(mount_obj, expected)

    def test_multiple_mounts(self):
        """``dockage`` 'mounts' parses a common, and mounts that path to multiple locations"""
        mount_dict = {'/home': '/home/bob,/home/jill'}

        mount_objs = dockage.mounts(mount_dict)
        expected = [docker.types.Mount(source='/home', target='/home/bob', type='bind'),
                    docker.types.Mount(source='/home', target='/home/jill', type='bind')]

        self.assertEqual(mount_objs, expected)

    def test_ro_mounts(self):
        """``dockage`` 'mounts' correctly parses and creates read only mounts"""
        mount_dict = {'/home': '/home:ro'}

        mount_obj = dockage.mounts(mount_dict)[0]
        expected = {'Target': '/home', 'Source': '/home', 'Type': 'bind', 'ReadOnly': True}

        self.assertEqual(mount_obj, expected)


class TestContainerCommand(unittest.TestCase):
    """A suite of test cases for the ``container_command`` function"""
    def test_create_no_command(self):
        """
        ``dockage`` 'container_command' returns the expected output when creating
        a user and logging them into a standard shell.
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='true',
                                        command='',
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = "/bin/bash -c '/usr/sbin/groupadd --gid 9001 liz && /sbin/adduser -m --uid 9001 --gid 9001 -s /bin/bash liz 2>/dev/null && chown liz:liz /dev/pts/0 2>/dev/null ; cd /home/liz 2>/dev/null ; /sbin/runuser liz -l '"

        self.assertEqual(cmd, expected)

    def test_no_create_no_command(self):
        """
        ``dockage`` 'container_command' results in the default CMD of the Docker
        image being executed by the image's default user when "create_user" and
        "command" are both false.
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='false',
                                        command='',
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = ""

        self.assertEqual(cmd, expected)

    def test_create_command(self):
        """
        ``dockage`` 'container_command' returns the expected output when creating
        a user and overriding the "shell"
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='true',
                                        command='/usr/local/bin/redis-cli',
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = '/bin/bash -c \'/usr/sbin/groupadd --gid 9001 liz && /sbin/adduser -m --uid 9001 --gid 9001 -s /bin/bash liz 2>/dev/null && chown liz:liz /dev/pts/0 2>/dev/null ; cd /home/liz 2>/dev/null ; /sbin/runuser liz -c "/usr/local/bin/redis-cli"\''

        self.assertEqual(cmd, expected)

    def test_no_create_command(self):
        """
        ``dockage`` 'container_command' returns the expected output when not creating
        a user and overriding the "shell"
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='false',
                                        command='/usr/local/bin/redis-cli',
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = "/usr/local/bin/redis-cli"

        self.assertEqual(cmd, expected)

    def test_escape_single_quotes(self):
        """
        ``dockage`` 'container_command' escapes single quotes when supplied
        with a command to execute
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='true',
                                        command="exec sh -c 'cd ; umask 077 ; mkdir -p .ssh'",
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = "/bin/bash -c \'/usr/sbin/groupadd --gid 9001 liz && /sbin/adduser -m --uid 9001 --gid 9001 -s /bin/bash liz 2>/dev/null && chown liz:liz /dev/pts/0 2>/dev/null ; cd /home/liz 2>/dev/null ; /sbin/runuser liz -c \"exec sh -c \'cd ; umask 077 ; mkdir -p .ssh\'\"\'"

        self.assertEqual(cmd, expected)

    def test_escape_double_quotes(self):
        """
        ``dockage`` 'container_command' escapes double quotes when supplied
        with a command to execute
        """
        cmd = dockage.container_command(username='liz',
                                        user_uid=9001,
                                        user_gid=9001,
                                        create_user='true',
                                        command='exec sh -c "cd ; umask 077 ; mkdir -p .ssh"',
                                        runuser='/sbin/runuser',
                                        useradd='/sbin/adduser')
        expected = '/bin/bash -c \'/usr/sbin/groupadd --gid 9001 liz && /sbin/adduser -m --uid 9001 --gid 9001 -s /bin/bash liz 2>/dev/null && chown liz:liz /dev/pts/0 2>/dev/null ; cd /home/liz 2>/dev/null ; /sbin/runuser liz -c "exec sh -c "cd ; umask 077 ; mkdir -p .ssh""\''

        self.assertEqual(cmd, expected)


class TestGenerateName(unittest.TestCase):
    """A suite of test cases for the ``generate_name`` function"""

    def test_generate_name(self, ):
        """``dockage`` 'generate_name' uses the username for shared environments."""
        output = dockage.generate_name('bob', command='')
        expected = 'bob'

        self.assertEqual(output, expected)

    @patch.object(dockage.uuid, 'uuid4')
    def test_generate_name_scp(self, fake_uuid4):
        """``dockage`` 'generate_name' creates a unique container name for SCP commands"""
        fake_uuid = MagicMock()
        fake_uuid.hex = 'aabbccddeeffgghh'
        fake_uuid4.return_value = fake_uuid

        output = dockage.generate_name('bob', command='scp')
        expected = 'bob-aabbcc'

        self.assertEqual(output, expected)

class TestQos(unittest.TestCase):
    """A suite of test cases for the ``qos`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.qos_params = _default()['qos']
        cls.fake_logger = MagicMock()

    def test_cpu(self):
        """``dockage`` 'qos' sets the CPU values correctly"""
        self.qos_params['cpus'] = '1.5'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'cpu_quota': 150000, 'cpu_period': 100000}

        self.assertEqual(qos_args, expected)

    def test_memory(self):
        """``dockage`` 'qos' sets the RAM values correctly"""
        self.qos_params['memory'] = '15g'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'mem_limit': '15g'}

        self.assertEqual(qos_args, expected)

    def test_device_read_iops(self):
        """``dockage`` 'qos' sets the device_read_iops values correctly"""
        self.qos_params['device_read_iops'] = '9001'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'device_read_iops' : [{'path': '/dev/sda', 'rate': 9001}]}

        self.assertEqual(qos_args, expected)

    def test_device_write_iops(self):
        """``dockage`` 'qos' sets the device_write_iops values correctly"""
        self.qos_params['device_write_iops'] = '9001'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'device_write_iops' : [{'path': '/dev/sda', 'rate': 9001}]}

        self.assertEqual(qos_args, expected)

    def test_device_read_bps(self):
        """``dockage`` 'qos' sets the device_read_bps values correctly"""
        self.qos_params['device_read_bps'] = '9001'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'device_read_bps' : [{'path': '/dev/sda', 'rate': 9001}]}

        self.assertEqual(qos_args, expected)

    def test_device_write_bps(self):
        """``dockage`` 'qos' sets the device_write_bps values correctly"""
        self.qos_params['device_write_bps'] = '9001'

        qos_args = dockage.qos(self.qos_params, self.fake_logger)
        expected = {'device_write_bps' : [{'path': '/dev/sda', 'rate': 9001}]}

        self.assertEqual(qos_args, expected)


class TestGetQosValue(unittest.TestCase):
    """A suite of test cases for the ``_get_qos_value`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.qos_params = _default()['qos']
        cls.fake_logger = MagicMock()

    def test_cast_string(self):
        """``dockage`` '_get_qos_value' can cast values to strings"""
        self.qos_params['memory'] = '1g'

        output = dockage._get_qos_value(self.qos_params,
                                        value_name='memory',
                                        value_type='string',
                                        logger=self.fake_logger)
        expected = '1g'

        self.assertEqual(output, expected)

    def test_cast_int(self):
        """``dockage`` '_get_qos_value' can cast values to integers"""
        self.qos_params['device_read_iops'] = '9001'

        output = dockage._get_qos_value(self.qos_params,
                                        value_name='device_read_iops',
                                        value_type='int',
                                        logger=self.fake_logger)
        expected = 9001

        self.assertEqual(output, expected)

    def test_cast_float(self):
        """``dockage`` '_get_qos_value' can cast values to floats"""
        self.qos_params['cpus'] = '1.8'

        output = dockage._get_qos_value(self.qos_params,
                                        value_name='cpus',
                                        value_type='float',
                                        logger=self.fake_logger)
        expected = 1.8

        self.assertEqual(output, expected)

    def test_cast_failure(self):
        """``dockage`` '_get_qos_value' returns None if unable to cast value"""
        self.qos_params['memory'] = '18m'

        output = dockage._get_qos_value(self.qos_params,
                                        value_name='memory',
                                        value_type='int',
                                        logger=self.fake_logger)
        expected = None

        self.assertEqual(output, expected)


    def test_cast_failure_log(self):
        """``dockage`` '_get_qos_value' logs the error if unable to cast value"""
        self.qos_params['memory'] = '18m'

        output = dockage._get_qos_value(self.qos_params,
                                        value_name='memory',
                                        value_type='int',
                                        logger=self.fake_logger)

        self.assertTrue(self.fake_logger.error.called)

class TestExecCommand(unittest.TestCase):
    """A suite of test cases for the ``exec_command`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.config = _default()
        cls.container = MagicMock()
        cls.container.image.attrs = {'Config': {'User' : '', 'Cmd' : ''}}

    def test_exec_command_default(self):
        """``dockage`` 'exec_command' Defaults to running a login shell"""
        syntax = dockage.exec_command(self.container, self.config, username='sally')
        expected = '/sbin/runuser -l sally'

        self.assertEqual(syntax, expected)

    def test_exec_command_cmd(self):
        """``dockage`` 'exec_command' executes a command as the user when supplied"""
        self.config['config']['command'] = '/bin/date'

        syntax = dockage.exec_command(self.container, self.config, username='sally')
        expected = '/sbin/runuser sally -c "/bin/date"'

        self.assertEqual(syntax, expected)

    def test_exec_command_no_user(self):
        """``dockage`` 'exec_command' uses the container's default user when not configure to create a user"""
        self.config['config']['create_user'] = 'false'

        syntax = dockage.exec_command(self.container, self.config, username='sally')
        expected = '/sbin/runuser -l root'

        self.assertEqual(syntax, expected)


class TestCreateExec(unittest.TestCase):
    """A suite of test cases for the ``create_exec`` function"""
    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.config = _default()
        cls.logger = MagicMock()
        cls.container = MagicMock()
        cls.container.id = 'aabbcc'
        cls.docker_client = MagicMock()
        cls.docker_client.api.exec_create.return_value = {'Id' : '1234abc'}

    @patch.object(dockage.sys.stdin, 'isatty')
    def test_create_exec(self, fake_isatty):
        """``dockage`` 'create_exec' TODO"""
        fake_isatty.return_value = True

        exec_id = dockage.create_exec(self.docker_client, self.container, self.config, 'bob', self.logger)
        expected = {'Id' : '1234abc'}

        self.assertEqual(exec_id, expected)


class TestShouldCreateUser(unittest.TestCase):
    """A suite of test cases for the ``_should_create_user`` function"""

    def test_returns_false(self):
        """``dockage`` '_should_create_user' returns False when supplied with the string "false" """
        result = dockage._should_create_user('false')

        self.assertFalse(result)

    def test_returns_true(self):
        """``dockage`` '_should_create_user' return True for basically anything that isn't "false" """
        results = []
        junk = ['f', 'null', ' false ', 'true', 't', 'banana', '0']
        for value in junk:
            result = dockage._should_create_user(value)
            results.append(result)

        self.assertTrue(all(results))



if __name__ == '__main__':
    unittest.main()
