# -*- coding: UTF-8 -*-
"""A suite of unit tests for the ``config.py`` module"""
import unittest
from unittest.mock import patch, MagicMock

from configparser import ConfigParser

from container_shell.lib import config


class TestDefault(unittest.TestCase):
    """A suite of test cases for the ``_default`` function"""
    def test_defaults(self):
        """``config`` The '_default' function returns the expected default config values"""
        test_config = ConfigParser()
        test_config.add_section('config')
        test_config.add_section('logging')
        test_config.add_section('dns')
        test_config.add_section('mounts')
        test_config.add_section('qos')
        test_config.add_section('binaries')

        test_config.set('config', 'image', 'debian:latest')
        test_config.set('config', 'hostname', 'someserver')
        test_config.set('config', 'auto_refresh', '')
        test_config.set('config', 'skip_users', '')
        test_config.set('config', 'create_user', 'true')
        test_config.set('config', 'command', '')
        test_config.set('config', 'term_signal', 'SIGHUP')
        test_config.set('logging', 'location', '/var/log/container_shell/messages.log')
        test_config.set('logging', 'max_size', '1024000') # 1MB
        test_config.set('logging', 'max_count', '3')
        test_config.set('logging', 'level', 'INFO')
        test_config.set('dns', 'servers', '')
        test_config.set('binaries', 'runuser', '/sbin/runuser')
        test_config.set('binaries', 'useradd', '/usr/sbin/useradd')

        default_config = config._default()

        self.assertEqual(test_config, default_config)

class TestGetConfig(unittest.TestCase):
    """A suite of test cases for the ``get_config`` function"""
    @patch.object(config.ConfigParser, 'read')
    def test_return_type(self, fake_read):
        """``config`` The 'get_config' function returns a tuple"""
        fake_read.return_value = False

        output = config.get_config()
        expected = (config._default(), True, '/etc/container_shell/config.ini')

        self.assertEqual(output, expected)

    @patch.object(config.ConfigParser, 'read')
    def test_using_defaults(self, fake_read):
        """
        ``config`` The 'get_config' function informs the caller if default
        values are being used.
        """
        fake_read.return_value = True

        _, using_default_values, _ = config.get_config()

        self.assertFalse(using_default_values)


    @patch.object(config.ConfigParser, 'read')
    def test_config_location(self, fake_read):
        """
        ``config`` The 'get_config' function informst the caller of the location
        for the configuration file.
        """
        fake_read.return_value = True

        _, _, config_location = config.get_config()
        expected = config.CONFIG_LOCATION

        self.assertEqual(config_location, expected)


if __name__ == '__main__':
    unittest.main()
