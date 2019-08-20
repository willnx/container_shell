# -*- coding: UTF-8 -*-
"""Generic functions that don't find into different modules"""
import os
import sys
import logging
import logging.handlers


def skip_container(username, skip_users):
    """Allows some users to access the host, instead of being dropped into a container

    :Returns: Boolean

    :param username: The name of the person running this code
    :type username: String

    :param skip_users: A comma-separated list of users to allow access to the host
    :type skip_users: String
    """
    return username in skip_users.split(',')


def printerr(message):
    """Just like print, except the message is delivered via stderr

    :Returns: None

    :param message: What to print to stderr
    :type message: String
    """
    sys.stderr.write('{}\n'.format(message))
    sys.stderr.flush()


class WorldWritableFileHandler(logging.handlers.RotatingFileHandler):
    """Creates a log file that any user can write to"""
    def _open(self):
        prev_umask = os.umask(0o001) # Make world writable
        log_fd = logging.handlers.RotatingFileHandler._open(self)
        os.umask(prev_umask) # Now set it back so we don't break stuff
        return log_fd


def get_logger(name, location, max_size, max_count, level=logging.INFO):
    """A simple factory to create file logging objects

    :Returns: logging.Logger

    :param name: The name of the log object.
    :type name: String

    :param location: The filesystem location to write the log messages to.
    :type location: String

    :param max_size: The number of bytes the file can grow to, before it's rotated.
    :type max_size: Integer

    :type max_count: The number of rotated log files to retain.
    :type max_count: Integer

    :param level: The verbosity of the logs
    :type level: Integer
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        channel = WorldWritableFileHandler(location,
                                           maxBytes=max_size,
                                           backupCount=max_count)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        channel.setLevel(level)
        channel.setFormatter(formatter)
        logger.addHandler(channel)
    return logger
