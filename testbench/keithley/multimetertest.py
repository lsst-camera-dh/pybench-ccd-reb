#! /usr/bin/env python


import sys, os, os.path
import time
import keithley2000 as multi


M = multi.Multimeter()

M.open()

M.reset()

start = time.time()

print "Test:"
M.setup(mode = "resistance", cycles = 0.1)
data = M.measure(count = 20, display = False)

stop = time.time()
time = stop - start

print "Time: ", time
print "Success!"

#M.close()
