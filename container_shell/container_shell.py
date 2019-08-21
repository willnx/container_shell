# -*- coding: UTF-8 -*-
"""Here we put everything together!"""
import os
import sys
import atexit
import signal
import argparse
import functools
import subprocess
from pwd import getpwnam
from getpass import getuser

import docker
import requests

from container_shell.lib.config import get_config
from container_shell.lib import utils, dockage, dockerpty

#pylint: disable=R0914
def main(cli_args=sys.argv[1:]):
    """Entry point logic"""
    user_info = getpwnam(getuser())
    username = user_info.pw_name
    user_uid = user_info.pw_uid
    args = parse_cli(cli_args)
    config, using_defaults, location = get_config(shell_command=args.command)
    docker_client = docker.from_env()
    logger = utils.get_logger(name=__name__,
                              location=config['logging'].get('location'),
                              max_size=config['logging'].getint('max_size'),
                              max_count=config['logging'].getint('max_count'),
                              level=config['logging'].get('level').upper())
    if using_defaults:
        logger.debug('No defined config file at %s. Using default values', location)

    if utils.skip_container(username, config['config']['skip_users']):
        logger.info('User %s accessing host environment', username)
        original_cmd = os.getenv('SSH_ORIGINAL_COMMAND', args.command)
        if not original_cmd:
            original_cmd = os.getenv('SHELL')
        proc = subprocess.Popen(original_cmd.split(), shell=sys.stdout.isatty())
        proc.communicate()
        sys.exit(proc.returncode)

    image = config['config'].get('image')
    if not config['config'].get('auto_refresh').lower() == 'false':
        try:
            docker_client.images.pull(image)
        except docker.errors.DockerException as doh:
            logger.exception(doh)
            utils.printerr('Unable to update login environment')
            sys.exit(1)

    kwargs = dockage.build_args(config, username, user_uid, logger)
    try:
        container = docker_client.containers.create(**kwargs)
    except docker.errors.DockerException as doh:
        logger.exception(doh)
        utils.printerr("Failed to create login environment")
        sys.exit(1)
    else:
        cleanup = functools.partial(kill_container,
                                    container,
                                    config['config']['term_signal'],
                                    logger)
        atexit.register(cleanup)
        # When OpenSSH detects that a client has disconnected, it'll send
        # SIGHUP to the process ran when that client connected.
        # If we don't handle this signal, then users who click the little "x"
        # on their SSH application (instead of pressing "CTL D" or typing "exit")
        # will cause ContainerShell to leak containers. In other words, the
        # SSH session will be gone, but the container will remain.
        set_signal_handlers(container, logger)
    try:
        dockerpty.start(docker_client.api, container.id)
        logger.info('Broke out of dockerpty')
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)
        utils.printerr("Failed to connect to PTY")
        sys.exit(1)


def set_signal_handlers(container, logger):
    """Set all the OS signal handlers, so we proxy signals to the process(es)
    inside the container

    :Returns: None

    :param container: The container created by ContainerShell
    :type container: docker.models.containers.Container

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    hupped = functools.partial(kill_container, container, 'SIGHUP', logger)
    signal.signal(signal.SIGHUP, hupped)
    interrupt = functools.partial(kill_container, container, 'SIGINT', logger)
    signal.signal(signal.SIGINT, interrupt)
    quit_handler = functools.partial(kill_container, container, 'SIGQUIT', logger)
    signal.signal(signal.SIGQUIT, quit_handler)
    abort = functools.partial(kill_container, container, 'SIGABRT', logger)
    signal.signal(signal.SIGABRT, abort)
    termination = functools.partial(kill_container, container, 'SIGTERM', logger)
    signal.signal(signal.SIGTERM, termination)


def kill_container(container, the_signal, logger):
    """Tear down the container when ContainerShell exits

    :Returns: None

    :param container: The container created by ContainerShell
    :type container: docker.models.containers.Container

    :param the_signal: The Linux SIGNAL to set to the container in order to stop it.
                       See "man signal" for details. Defaults to SIGHUP.
    :type the_signal: String

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    try:
        container.exec_run('kill -{} 1'.format(the_signal))
    except requests.exceptions.HTTPError as doh:
        if doh.response.status_code == 409:
            # the container is already stopped
            pass
        else:
            logger.exception(doh)
    try:
        container.kill()
    except requests.exceptions.HTTPError as doh:
        status_code = doh.response.status_code
        #pylint: disable=R1714
        if status_code == 404 or status_code == 409:
            # Container is already deleted, or stopped
            pass
        else:
            logger.info(dir(doh))
            logger.exception(doh)
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)
    try:
        container.remove()
    except docker.errors.NotFound:
        pass
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)


def parse_cli(cli_args):
    """Intemperate the CLI arguments, and return a useful object

    :Returns: argparse.Namespace

    :param cli_args: The command line arguments supplied to container_shell
    :type cli_args: List
    """
    description = 'A mostly transparent proxy to an isolated shell environment.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--command', default='',
                        help='Execute a specific command, then terminate.')

    args = parser.parse_args(cli_args)
    return args


if __name__ == '__main__':
    main()
