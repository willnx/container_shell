#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Defines parameters when building the container-shell package"""
from setuptools import find_packages, setup

with open('VERSION') as the_file:
    version = the_file.read().strip()

setup(name="container-shell",
      author="Nicholas Willhite,",
      author_email='willnx84@gmail.com',
      version=version,
      packages=find_packages(),
      description="SSH logins drop users into a docker environment",
      install_requires=['docker', 'six'],
      entry_points={'console_scripts' : 'container_shell=container_shell.container_shell:main'}
      )
