# -*- coding: UTF-8 -*-
"""Here we put everything together!"""
import os
import re
import sys
import time
import atexit
import signal
import argparse
import functools
import subprocess
from pwd import getpwnam
from getpass import getuser

import docker

from container_shell.lib.config import get_config
from container_shell.lib import utils, dockage, dockerpty

#pylint: disable=R0914,R0915,W0102
def main(cli_args=sys.argv[1:]):
    """Entry point logic"""
    user_info = getpwnam(getuser())
    username = user_info.pw_name
    user_uid = user_info.pw_uid
    user_gid = user_info.pw_gid
    args = parse_cli(cli_args)

    config, using_defaults, location = get_config(shell_command=args.command)
    docker_client = docker.from_env(timeout=config['config'].getint('docker_timeout'))
    logger = utils.get_logger(name=__name__,
                              location=config['logging'].get('location'),
                              max_size=config['logging'].getint('max_size'),
                              max_count=config['logging'].getint('max_count'),
                              level=config['logging'].get('level').upper())
    logger.debug("CLI Args: %s", args)
    if using_defaults:
        logger.debug('No defined config file at %s. Using default values', location)
    else:
        logger.debug('Custom config:\n%s', config)

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

    try:
        create_kwargs = dockage.build_args(config, username, user_uid, user_gid, logger)
        logger.debug('Create kwargs:\n%s', create_kwargs)
        container, standalone = _get_container(docker_client, username, config, **create_kwargs)
    except docker.errors.DockerException as doh:
        logger.exception(doh)
        utils.printerr("Failed to create login environment")
        sys.exit(1)
    else:
        cleanup = functools.partial(kill_container,
                                    container,
                                    config['config']['term_signal'],
                                    config['config']['persist'],
                                    config['config']['persist_egrep'],
                                    config['binaries']['ps'],
                                    logger)
        atexit.register(cleanup)
    try:
        if standalone:
            logger.debug("Connecting to standalone container")
            # When OpenSSH detects that a client has disconnected, it'll send
            # SIGHUP to the process ran when that client connected.
            # If we don't handle this signal, then users who click the little "x"
            # on their SSH application (instead of pressing "CTL D" or typing "exit")
            # will cause ContainerShell to leak containers. In other words, the
            # SSH session will be gone, but the container will remain.
            set_container_signal_handlers(container, config, logger)
            dockerpty.start(docker_client.api, container.id)
        else:
            logger.debug("Connecting to shared container")
            exec_id = dockage.create_exec(docker_client, container, config, username, logger)
            set_exec_signal_handlers(docker_client, exec_id, logger)
            exec_op = dockerpty.pty.ExecOperation(docker_client.api, exec_id, logger)
            dockerpty.pty.PseudoTerminal(docker_client.api, exec_op).start()
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)
        utils.printerr("Failed to connect to PTY")
        sys.exit(1)


def _get_container(docker_client, username, config, **create_kwargs):
    """Find or create the Linux container to operate against.

    :Returns: Tuple

    :param docker_client: For communicating with the Docker daemon.
    :type docker_client: docker.client.DockerClient

    :param username: The name of the user running Container Shell.
    :type username: String

    :param config: The defined settings (or defaults) that define the behavior of Container Shell.
    :type config: configparser.ConfigParser
    """
    standalone = False
    command = config['config']['command']
    if command.startswith('scp') or command.endswith('sftp-server'):
        # Not sure why, but I can only get `scp` to work via it's own container.
        # Hacky, but if you can fix please let me know!
        container = docker_client.containers.create(**create_kwargs)
        standalone = True
    else:
        for container in docker_client.containers.list(all=True):
            if container.name == username:
                break
        else:
            container = docker_client.containers.create(**create_kwargs)

    if container.status == 'created' and not standalone:
        # Correctly handles two different situations:
        #   1) A new container was just created.
        #   2) for whatever reason, the container exists but was stopped.
        # Two containers with the same name cannot exist. If the server was
        # suddenly rebooted, users might be unable to connect because their
        # old session exists, it's just not running.
        container.start()
        _block_on_init(container, username, config['binaries']['id'])
    return container, standalone


def _block_on_init(container, username, id_path, timeout=60):
    """There's a race between starting the container and creating the user inside
    it, and running the ``exec`` against the container to connect the user to it.


    :Returns: None

    :param container: The container created by ContainerShell
    :type container: docker.models.containers.Container

    :param username: The name of the user running Container Shell.
    :type username: String

    :param id_path: The location of the ``id`` command/binary
    :type id_path: String

    :param timeout: Maximum number of seconds to block
    :type timeout: Integer
    """
    start_time = time.time()
    command = '{} {}'.format(id_path, username)
    still_making = container.exec_run(command).exit_code
    while still_making:
        time.sleep(0.1)
        if (time.time() - start_time) > timeout:
            raise RuntimeError('Failed to create user within {} seconds'.format(timeout))
        still_making = container.exec_run(command).exit_code


def set_container_signal_handlers(container, config, logger):
    """Set all the OS signal handlers, so we proxy signals to the process(es)
    inside the container.

    :Returns: None

    :param container: The container created by ContainerShell
    :type container: docker.models.containers.Container

    :param config: The defined settings (or defaults) that define the behavior of Container Shell.
    :type config: configparser.ConfigParser

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    persist = config['config']['persist']
    persist_egrep = config['config']['persist_egrep']
    ps_path = config['binaries']['ps']
    hupped = functools.partial(kill_container, container, 'SIGHUP', persist, persist_egrep, ps_path, logger) #pylint: disable=C0301
    signal.signal(signal.SIGHUP, hupped)
    interrupt = functools.partial(kill_container, container, 'SIGINT', persist, persist_egrep, ps_path, logger) #pylint: disable=C0301
    signal.signal(signal.SIGINT, interrupt)
    quit_handler = functools.partial(kill_container, container, 'SIGQUIT', persist, persist_egrep, ps_path, logger) #pylint: disable=C0301
    signal.signal(signal.SIGQUIT, quit_handler)
    abort = functools.partial(kill_container, container, 'SIGABRT', persist, persist_egrep, ps_path, logger) #pylint: disable=C0301
    signal.signal(signal.SIGABRT, abort)
    termination = functools.partial(kill_container, container, 'SIGTERM', persist, persist_egrep, ps_path, logger) #pylint: disable=C0301
    signal.signal(signal.SIGTERM, termination)


def set_exec_signal_handlers(docker_client, exec_id, logger):
    """Propagate signals to the PID for the ``docker exec`` instance.

    This is mostly for OpenSSH support. So regardless of the program you run
    inside the container, any of the "tear down" signals get cast to SIGTERM.

    :Returns: None

    :param docker_client: For communicating with the Docker daemon.
    :type docker_client: docker.client.DockerClient

    :param exec_id: The Id -> hex mapping for the exec id.
    :type exec_id: Dictionary

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    logger.info("Setting EXEC signal handlers")
    exec_handle = functools.partial(kill_exec, docker_client, exec_id, logger)
    signal.signal(signal.SIGHUP, exec_handle)
    signal.signal(signal.SIGINT, exec_handle)
    signal.signal(signal.SIGQUIT, exec_handle)
    signal.signal(signal.SIGABRT, exec_handle)
    signal.signal(signal.SIGTERM, exec_handle)


def ignore_not_found(func):
    """Avoids SPAM when attempting to kill an auto-removed container"""
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            resp = func(*args, **kwargs)
        except docker.errors.NotFound:
            pass
        else:
            return resp
    return inner


@ignore_not_found
def _should_not_kill(container, persist, persist_egrep, ps_path, logger):
    """Inspect the process table for backgroung programs when configured to persist containers

    :Returns: Boolean

    :param container: The container a user was connected to.
    :type container: docker.models.containers.Container

    :param persist: The config setting that defines if Container Shell should
                    keep the container after a user disconnects.
    :type persist: String

    :param persist_egrep: The egrep-like syntax to search the proces
    :type persist_egrep: String

    :param ps_path: The absolute path location to the ``ps`` command in the container.
    :type ps_path: String

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    ps_cmd = '{} auxwww'.format(ps_path.replace(';', ''))
    regex = re.compile('({})'.format(persist_egrep))
    _, ps_output = container.exec_run(ps_cmd)
    # Minimizes the race between two sessions terminating at nearly the same time.
    # If `container.exec_run(ps_cmd)` was ran after the `container.reload()` and inspecting
    # it for execution IDs, then it's possible that a this thread's check of the container's
    # process table could be interpreted as an active session to another thread that's
    # terminating it's session just after this one. The result is that the container is kept
    # when it should be deleted.
    container.reload()
    #pylint: disable=R1705
    if container.attrs['ExecIDs']:
        # There's "other" connections to that environment, so don't nuke the environment.
        return True
    elif persist.lower().startswith('f'):
        return False
    else:
        found = re.search(regex, ps_output.decode(errors='ignore'))
        logger.debug("Persistence search results: %s", found)
        return bool(found)

#pylint: disable=R0913
def kill_container(container, the_signal, persist, persist_egrep, ps_path, logger):
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
    if _should_not_kill(container, persist, persist_egrep, ps_path, logger):
        return
    logger.debug('Tearing down container')
    try:
        container.exec_run('kill -{} 1'.format(the_signal))
    except docker.errors.APIError as doh:
        status_code = doh.response.status_code
        #pylint: disable=R1714
        if status_code == 404 or status_code == 409:
            # Container is already deleted, or stopped
            pass
        else:
            logger.exception(doh)
    try:
        container.remove()
    except docker.errors.NotFound:
        pass
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)

#pylint: disable=W0613
def kill_exec(docker_client, exec_id, logger, *args, **kwargs):
    """Send SIGTERM to terminate the PID from the ``docker exec`` instance.

    :Returns: None

    :param docker_client: For communicating with the Docker daemon.
    :type docker_client: docker.client.DockerClient

    :param exec_id: The Id -> hex mapping for the exec id.
    :type exec_id: Dictionary

    :param logger: An object for writing errors/messages for debugging problems
    :type logger: logging.Logger
    """
    pid = int(docker_client.api.exec_inspect(exec_id['Id'])['Pid'])
    os.kill(pid, 15) #SIGTERM
    cycles = _block_on_pid(pid)
    logger.debug("Exec blocked for %s sec on pid %s to exit gracefully", cycles, pid)


def _block_on_pid(pid):
    """It can take a few seconds for the process to gracefully exit.

    Waits upwards of 60 seconds for the process to terminate. Returns the number
    of seconds the pid took to terminate.

    :Returns: Integer

    :param pid: The process ID of the ``docker exec`` instance.
    :type pid: Integer
    """
    for i in range(60):
        try:
            os.kill(pid, 0) # signal zero does nothing
        except ProcessLookupError:
            break
        else:
            time.sleep(1)
    return i


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
