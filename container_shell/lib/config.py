# -*- coding: UTF-8 -*-
"""Read the user-defined config file to dictate how to launch the continer"""
from configparser import ConfigParser

CONFIG_LOCATION = '/etc/container_shell/config.ini'


def get_config(shell_command='', location=CONFIG_LOCATION):
    """Read the supplied INI file, and return a usable object

    :Returns: configparser.ConfigParser

    :param shell_command: Override the command to run in the shell with whatever
                          gets supplied via the CLI.
    :type shell_command: String

    :param location: The location of the config.ini file
    :type location: String
    """
    config = _default()
    using_defaults = False
    # Reading a user-defined config will cause any default values to be replaced
    # by the user-defined values.
    if not config.read(location):
        # no config file exists. This section exists so we can communicate that
        # back up the stack.
        using_defaults = True
    if shell_command:
        config['config']['command'] = shell_command
    return config, using_defaults, location


def _default():
    """Ensure the config object has the required minimum definitions

    :Returns: configparser.ConfigParser

    :param config: The config object to mutate
    :type config: configparser.ConfigParser
    """
    config = ConfigParser()
    config.add_section('config')
    config.add_section('logging')
    config.add_section('dns')
    config.add_section('mounts')
    config.add_section('qos')
    config.add_section('binaries')

    config.set('config', 'image', 'debian:latest')
    config.set('config', 'hostname', 'someserver')
    config.set('config', 'auto_refresh', '')
    config.set('config', 'skip_users', '')
    config.set('config', 'create_user', 'true')
    config.set('config', 'command', '')
    config.set('config', 'term_signal', 'SIGHUP')
    config.set('logging', 'location', '/var/log/container_shell/messages.log')
    config.set('logging', 'max_size', '1024000') # 1MB
    config.set('logging', 'max_count', '3')
    config.set('logging', 'level', 'INFO')
    config.set('dns', 'servers', '')
    config.set('binaries', 'runuser', '/sbin/runuser')
    config.set('binaries', 'useradd', '/usr/sbin/useradd')

    return config
