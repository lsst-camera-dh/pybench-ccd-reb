#! /usr/bin/env python


import sys, os, os.path
import time
import sp_dk240 as mono


M = mono.Monochromator(port = '/dev/ttyUSB0')

M.open()

#wavelength = M.get_wavelength()
#print "Current wavelength = ", wavelength

#print "Changing wavelength to 483 nm..."
#M.set_allslit(1.)

width = M.get_slit()
print "Current widthness = ", width

start = time.time()

value = 1000
M.set_exit_slit(value)
print "Changing all slits to:", value
stop = time.time()

time = stop - start
print "Operation time", time
print "Success !"

M.close()


