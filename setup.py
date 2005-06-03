#! /usr/bin/env python
# 
# $Id$
#

import sys,os

sys.path.insert(0,os.getcwd())

from distutils.core import setup

import SRS

setup(
        #-- Package description
        name = 'pysrs',
        license = 'Python license',
        version = SRS.__version__,
        description = 'Python SRS (Sender Rewriting Scheme) library',
        long_description = """Python SRS (Sender Rewriting Scheme) library.
As SPF is implemented, mail forwarders must rewrite envfrom for domains
they are not authorized to send from.

See http://spf.pobox.com/srs.html for details.
The Perl reference implementation is at http://www.anarres.org/projects/srs/
""",
        author = 'Stuart Gathman (Perl version by Shevek)', 
        author_email = 'stuart@bmsi.com',
        url = 'http://bmsi.com/python/pysrs.html',
        packages = ['SRS'],
	scripts = ['envfrom2srs.py','srs2envtol.py'],
	keywords = ['SPF','SRS'],
	classifiers = [
	  'Development Status :: 4 - Beta',
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
