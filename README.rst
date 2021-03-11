.. image:: https://travis-ci.org/willnx/container_shell.svg?branch=master
    :target: https://travis-ci.org/willnx/container_shell

.. image:: https://coveralls.io/repos/github/willnx/container_shell/badge.svg
    :target: https://coveralls.io/github/willnx/container_shell


###############
Container Shell
###############
Container Shell was inspired by `Yelp/dockersh <https://github.com/Yelp/dockersh>`_,
and allows an admin of a system to manage how a user can access a specific
Docker container. You can use Container Shell like a normal executable, configure it
as a user's shell (via ``/etc/passwd``), or upon SSH logins with the
`ForceCommand <https://linux.die.net/man/5/sshd_config>`_ keyword in the
``/etc/sshd_config`` file.


Under the hood
==============
Normally, to run a docker command you need to  be ``root`` or part of the
``docker`` group
(which `effectively is root <https://docs.docker.com/engine/security/security/>`_).
Container Shell avoids this by leveraging the `setuid <https://en.wikipedia.org/wiki/Setuid>`_
permission, allowing an unprivileged user the ability to access a admin-defined container.


Installing
==========
Container Shell is distributed as both an
`RPM <https://en.wikipedia.org/wiki/RPM_Package_Manager>`_  and a
`deb <https://en.wikipedia.org/wiki/Deb_(file_format)>`_. Just download the
one that works for your OS from the `Releases <https://github.com/willnx/container_shell/releases>`_
page and install it like any other package!


Configuring the container
=========================
The only configuration file for Container Shell is located at
``/etc/container_shell/config.ini``. It's in a standard
`INI <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_
format, so it's easy to modify.

If no file exists, then Container Shell will assume some defaults. The main
section you'll want to adjust for your installation is the ``config`` section,
where you can define which container image a user will be placed into. By default,
Container Shell will use the latest `debian <https://www.debian.org/>`_ image.

A sample config is installed to ``/etc/container_shell/sample.config.ini``, which
will have additional context. But if you're checking out the repo, the sample
is right in the source ^^.


Handy Tips
==========
This section contains some useful commands to inspect Container Shell sessions.


Who's using it?
---------------
The containers created by Container Shell combine the name of the user who ran
the command along with some random HEX characters. This means that as an admin,
it's really easy to see *who's using Container Shell*; just run:

.. code-block:: shell

    $ docker ps --format '{{.ID}}: {{.Names}}'

That command will output the container ID followed by the container's name,
separated by a colon (``:``).


Who's using all the resources?
------------------------------
If you haven't configured any `QoS <https://en.wikipedia.org/wiki/Quality_of_service>`_
options in the ``/etc/container_shell/config.ini``, you can leverage this command
to see how much CPU, RAM, and IO each container is using:

.. code-block:: shell

   $ docker stats


What's that user doing in their container?
------------------------------------------
You can leverage the `docker exec <https://docs.docker.com/engine/reference/commandline/exec/>`_
command to inspect what users are running inside their containers.

To start, you'll need the container ID. In this example output, the container ID
is ``4523b2ef295d``::

  $ docker ps
  CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
  4523b2ef295d        centos:latest       "/bin/bash -c '/usr/…"   2 days ago          Up 2 days                               bob-d88c70

Once you have the container Id, just use the `ps <http://man7.org/linux/man-pages/man1/ps.1.html>`_
command to inspect it::

  $ docker exec 4523b2ef295d ps auxwww
