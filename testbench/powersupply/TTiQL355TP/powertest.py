#! /usr/bin/env python

#
# Tests of TTiQL355TP Python module.
#


import sys, os, os.path
import time
import TTiQL355TP as power


P = power.PowerSupply(port = '/dev/ttyUSB-TTiQL355TP')

P.open()

start = time.time()

print "Test #1:"
P.reset()
P.set_V(2,3.5)
P.set_I(1,2.)
P.on(1)
P.off(1)
P.on('all')

stop = time.time()

time = stop - start
print "Operation time: ", time
print "Success!"

print "Test #2:"

try:
    P.set_V(1,55.0)
except power.PowerSupplyError, e:
    print "Setting failed, exception has been caught:" 
    print e


print "Success!"

P.close()
