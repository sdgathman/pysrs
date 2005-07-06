__version__ = '0.30.10'

__all__= [
  'new',
  '__version__'
]

import ses

def new(secret=None,*args,**kw):
  return ses.SES(secret,*args,**kw)
