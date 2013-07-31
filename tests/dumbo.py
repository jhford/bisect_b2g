#!/usr/bin/env python

import sys
from optparse import OptionParser

parser = OptionParser("%prog - I am dumbo the dumb program")
parser.add_option("--exit-code", dest="exit_code", type='int')
opts, args = parser.parse_args()
for arg in args:
    if arg.startswith('STDERR:'):
        sys.stderr.write(arg[7:] + '\n')
    elif arg.startswith('STDOUT:'):
        sys.stdout.write(arg[7:] + '\n')
    else:
        sys.stdout.write(arg + '\n')
    sys.stdout.flush()
    sys.stderr.flush()
exit(opts.exit_code)
