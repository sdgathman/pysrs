#! /usr/bin/env python
# 
# $Id$
#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import sys,os

sys.path.insert(0,os.getcwd())

from setuptools import setup

import SRS

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
        #-- Package description
        name = 'pysrs',
        license = 'Python license',
        version = '1.0.4',
        description = 'Python SRS (Sender Rewriting Scheme) library',
        long_description = long_description,
        author = 'Stuart Gathman (Perl version by Shevek)', 
        author_email = 'stuart@gathman.org',
        url = 'https://pymilter.org/milter/pysrs.html',
        py_modules = ['SocketMap'],
        packages = ['SRS','SES'],
        scripts = ['envfrom2srs.py','srs2envtol.py'],
        keywords = ['SPF','SRS','SES'],
        classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: No Input/Output (Daemon)',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python License (CNRI Python License)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Communications :: Email',
          'Topic :: Communications :: Email :: Mail Transport Agents',
          'Topic :: Software Development :: Libraries :: Python Modules'
        ]
)
