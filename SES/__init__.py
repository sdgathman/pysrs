#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.
__version__ = '1.0'

__all__= [
  'new',
  '__version__'
]

from . import ses

def new(secret=None,*args,**kw):
  return ses.SES(secret,*args,**kw)
