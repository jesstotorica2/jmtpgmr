import sys
from . import jmtpgmr
#import jmtpgmr

rc = 1
try:
  jmtpgmr.cli(prog_name='jmtpgmr')
  rc = 0
except Exception as e:
  print('Error: %s' % e, file=sys.stderr)
sys.exit(rc)
