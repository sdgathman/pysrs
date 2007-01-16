# $Log$
# Revision 1.3  2006/02/16 05:21:25  customdesigned
# Support SRS signing mode.
#
# Revision 1.2  2005/08/11 23:35:32  customdesigned
# SES support.
#
# Revision 1.1.1.2  2005/06/03 04:13:56  customdesigned
# Support sendmail socketmap
#
# Revision 1.6  2004/08/26 03:31:38  stuart
# Introduce sendmail socket map
#
# Revision 1.5  2004/06/09 00:32:05  stuart
# Release 0.30.8
#
# Revision 1.4  2004/03/24 23:59:42  stuart
# Release 0.30.7
#
# Revision 1.3  2004/03/23 20:36:39  stuart
# Version 0.30.6
#
# Revision 1.2  2004/03/22 18:20:19  stuart
# Missing import
#
# Revision 1.1.1.1  2004/03/19 05:23:13  stuart
# Import to CVS
#
#
# AUTHOR
# Shevek
# CPAN ID: SHEVEK
# cpan@anarres.org
# http://www.anarres.org/projects/
#
# Translated to Python by stuart@bmsi.com
# http://bmsi.com/python/milter.html
#
# Portions Copyright (c) 2004 Shevek. All rights reserved.
# Portions Copyright (c) 2004 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

__version__ = '0.30.12'

__all__= [
  'Base',
  'Guarded',
  'Shortcut',
  'Reversible',
  'Daemon',
  'DB',
  'new',
  'SRS0TAG',
  'SRS1TAG',
  'SRSSEP',
  'SRSHASHLENGTH',
  'SRSMAXAGE',
  '__version__'
]

SRS0TAG = 'SRS0'
SRS1TAG = 'SRS1'
SRSSEP = '='
SRSHASHLENGTH = 4
SRSMAXAGE = 21

#from Base import SRS
#from Guarded import Guarded
#from Shortcut import Shortcut
#from Reversible import Reversible
#from Daemon import Daemon
#from DB import DB
import Guarded

def new(secret=None,*args,**kw):
  return Guarded.Guarded(secret,*args,**kw)
