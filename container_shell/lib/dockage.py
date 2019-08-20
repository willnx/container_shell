# -*- coding: UTF-8 -*-
"""Functions to help construct the docker container"""
import sys
import uuid

import docker


def build_args(config, username, user_uid, logger):
    """Construct the arguments to use when creating the container

    :Returns: Dictionary

    :param config: The defined settings (or defaults) to use when creating the container
    :type config: configparser.ConfigParser
    """
    qos_args = qos(config['qos'], logger)
    container_kwargs = {
        'image' : config['config'].get('image'),
        'hostname' : config['config'].get('hostname'),
        'tty' : sys.stdout.isatty(),
        'init' : True,
        'stdin_open' : True,
        'dns' : dns(config['dns']['servers']),
        'mounts' : mounts(config['mounts']),
        'command' : container_command(username=username,
                                      user_uid=user_uid,
                                      create_user=config['config']['create_user'],
                                      command=config['config']['command'],
                                      runuser=config['binaries']['runuser'],
                                      useradd=config['binaries']['useradd']),
        'name' : generate_name(username),
    }
    container_kwargs.update(qos_args)
    return container_kwargs


def dns(addrs):
    """Formats the usage of DNS servers.

    Very important to define this parameter when ever running a container as
    Ubuntu resolves over the loopback network, and RHEL doesn't.

    If you don't supply this in a docker run command, than users running RHEL
    based Linux cannot run automation built from Ubuntu based containers.
    Same thing for Ubuntu OS users running RHEL based containers.

    :Returns: String

    :param addrs: A comma separated list of DNS IPs
    :type addrs: String
    """
    if addrs:
        return [x.strip(' \n') for x in addrs.split(',')]
    return None


def mounts(mount_dict):
    """Formats the usage of local file system mounts to the container's file system.

    Automatically handles users running SELinux by adding the ':Z' option on
    ``mount`` (which is needed in SELinux if the container needs write permissions).

    :Returns: String

    :param mount_dict: **Required** A key is the local file system location.
                       A value is the container file system location.

                       Example: {'/home/bob' : /mnt/container}
                       This will allow writes within the container to /mnt/container
                       to persist under /home/bob on the local file system.
    :type mount_dict: Dictionary
    """
    the_mounts = []
    for local_dir, container_dir in mount_dict.items():
        a_mount = docker.types.Mount(source=local_dir,
                                     target=container_dir,
                                     type='bind')
        the_mounts.append(a_mount)
    return the_mounts

#pylint: disable=R0913
def container_command(username, user_uid, create_user, command, runuser, useradd):
    """Constructs the command to run within the container.

    Command created will create a user to execute a command within the container.
    This makes the container more seamless to the end user, and avoids all files
    being written by different users having the same ownership on the host system.

    :Returns: String

    :param username: **Required** The name of user to create within the container
    :type username: String

    :param user_uid: **Required** The UID of the user to create within the container
    :Type user_uid: Integer

    :param create_user: Recreate the user identity inside the new container, and
                        run the shell as that user.
    :type create_user: Boolean

    :param command: Override the default login shell.
    :type command: String

    :param runuser: **Required** The absolute file path to the ``runuser`` command
                    inside the container
    :type runuser: String

    :param useradd: **Required** The absolute file path to the ``useradd`` command
                    inside the container
    :type usseradd: String
    """
    # the config object has a terrible "return binary" function, so check the
    # literal string value... Checking for "not false" makes it default to create
    # the user, which is a safer default should a sys admin typo the config.
    if create_user.lower() != 'false':
        if command:
            run_user = "{0} {1} -c \"{2}\"".format(runuser, username, command)
        else:
            # if not a specific command, treat this as a login shell
            run_user = '{0} {1} -l {2}'.format(runuser, username, command)
        make_user = '{0} -m -u {1} -s /bin/bash {2} 2>/dev/null'.format(useradd, user_uid, username)

        #everything = "/bin/bash -c '{0} && {1}'".format(make_user, run_user)
        everything = "/bin/bash -c '{} && {}'".format(make_user, run_user)
    elif command:
        everything = command
    else:
        everything = '' # use the container default
    return everything


def generate_name(username):
    """Assign a name to the container.

    The name created is a combination of the username of the person creating a
    container, and a random chunk of HEX characters. The username makes it easy
    for an admin to know *who's logged in* by running ``docker ps``. The random
    HEX enables a user to have multiple container sessions (because containers must
    have unique names).

    :Returns: String

    :param username: The user SSHing into the system
    :type username: String
    """
    unique_id = uuid.uuid4().hex[:6]
    return '{}-{}'.format(username, unique_id)


def qos(qos_params, logger):
    """Construct the Quality of Service arguments to limit the container resources.

    :Returns: String

    :param qos_params: The Quality of Service arguments to values mapping
    :type qos_params: Dictionary

    :param logger: An object for writing messages to a log file
    :type logger: logging.Logger
    """
    qos_args = {}
    # https://docs.docker.com/config/containers/resource_constraints/
    scheduler_period = 100000
    default_device = '/dev/sda'
    cpu_quota = _get_qos_value(qos_params, 'cpus', 'float', logger)
    if cpu_quota:
        qos_args['cpu_quota'] = int(cpu_quota * scheduler_period) # API takes an Int
        qos_args['cpu_period'] = scheduler_period
    memory = _get_qos_value(qos_params, 'memory', 'string', logger)
    if memory:
        qos_args['mem_limit'] = memory
    device_read_iops = _get_qos_value(qos_params, 'device_read_iops', 'int', logger)
    if device_read_iops:
        qos_args['device_read_iops'] = [{'path': default_device, 'rate': device_read_iops}]
    device_write_iops = _get_qos_value(qos_params, 'device_write_iops', 'int', logger)
    if device_write_iops:
        qos_args['device_write_iops'] = [{'path': default_device, 'rate': device_write_iops}]
    device_read_bps = _get_qos_value(qos_params, 'device_read_bps', 'int', logger)
    if device_read_bps:
        qos_args['device_read_bps'] = [{'path': default_device, 'rate': device_read_bps}]
    device_write_bps = _get_qos_value(qos_params, 'device_write_bps', 'int', logger)
    if device_write_bps:
        qos_args['device_write_bps'] = [{'path': default_device, 'rate': device_write_bps}]
    return qos_args


def _get_qos_value(qos_params, value_name, value_type, logger):
    """Obtain a Quality of Service parameter from the configuration object.

    Gracefully handles invalid types by logging a handy message, and simply
    returning None (which the caller should ignore).

    :Returns: PyObject

    :param qos_parms: The values under the 'qos' section of the config INI
    :type qos_params: configparser.SectionProxy
    """
    value = None
    if value_type == 'string':
        caster = str
    elif value_type == 'int':
        caster = int
    elif value_type == 'float':
        caster = float
    try:
        value = qos_params.get(value_name, None)
        if value:
            value = caster(value)
    except ValueError:
        value = None
        msg = "Invalid value supplied in INI section 'qos' for key {}".format(value_name)
        logger.error("%s: Supplied: %s, expected %s", msg, qos_params.get('cpus'), value_type)
    return value
