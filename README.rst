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
Container Shell avoids this by leveraging the `setgid <https://en.wikipedia.org/wiki/Setuid>`_
permission, allowing a user that is not part of the ``docker`` group the ability
to access a admin-defined container.


Installing
==========
Container Shell is distributed as both an
`RPM <https://en.wikipedia.org/wiki/RPM_Package_Manager>`_  and a
`deb <https://en.wikipedia.org/wiki/Deb_(file_format)>`_. Just download the
one that works for your OS, and install it like any other package!


Configuring the container
=========================
The only configuration file for Container Shell is located at
``/etc/container_shell/config.ini``. It's in a standard
`INI <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_
format, so it's easy to modify.

If no file exists, then Container Shell will assume some defaults. The main
section you'll want to adjust for your installation is the ``config`` section,
where you can define which container image a user will be placed into. By default,
Container Shell will use `busybox <https://hub.docker.com/_/busybox>`_ (just
because it's so small).

A sample config is installed to ``/etc/container_shell/sample.config.ini``, which
will have additional context. But if you're checking out the repo, the sample
is right in the source ^^.
