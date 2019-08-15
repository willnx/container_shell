# -*- coding: UTF-8 -*-
"""Here we put everything together!"""
import os
import sys
import subprocess
from pwd import getpwnam
from getpass import getuser

import docker

from container_shell.lib.config import get_config
from container_shell.lib import utils, dockage, dockerpty

#pylint: disable=R0915
#pylint: disable=R0912
def main():
    """Entry point logic"""
    user_info = getpwnam(getuser())
    username = user_info.pw_name
    user_uid = user_info.pw_uid
    config, using_defaults, location = get_config()
    docker_client = docker.from_env()
    logger = utils.get_logger(name=__name__,
                              location=config['logging'].get('location'),
                              max_size=config['logging'].getint('max_size'),
                              max_count=config['logging'].getint('max_count'),
                              level=config['logging'].get('level').upper())
    if using_defaults:
        logger.debug('No defined config file at %s. Using default values', location)

    original_cmd = os.getenv('SSH_ORIGINAL_COMMAND', '')
    if original_cmd.startswith('scp') or original_cmd.endswith('sftp-server'):
        if config['config']['disable_scp']:
            utils.printerr('Unable to SCP files onto this system. Forbidden.')
            sys.exit(1)
        else:
            logger.debug('Allowing %s to SCP file. Syntax: %s', username, original_cmd)
            returncode = subprocess.call(original_cmd.split())
            sys.exit(returncode)

    if utils.skip_container(username, config['config']['skip_users']):
        logger.info('User %s accessing host environment', username)
        if not original_cmd:
            original_cmd = os.getenv('SHELL')
        proc = subprocess.Popen(original_cmd.split(), shell=True)
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
    try:
        dockerpty.start(docker_client.api, container.id)
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)
        utils.printerr("Failed to connect to PTY")
        sys.exit(1)
    try:
        container.kill()
    except docker.errors.NotFound:
        pass
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)
    try:
        container.remove()
    except docker.errors.NotFound:
        pass
    except Exception as doh: #pylint: disable=W0703
        logger.exception(doh)


if __name__ == '__main__':
    main()
