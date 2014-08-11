#! /usr/bin/env python

import sys
import time

import xmlrpclib

import lsst.instruments.utils.grid as grid


xyz = xmlrpclib.ServerProxy("http://lpnlsst:8101/")

print "XYZ: opening connection..."
xyz.open()
print "XYZ: connection established."

print "XYZ: homing procedure..."
xyz.home()
print "XYZ at home."

print "XYZ position is now ", xyz.get_position()


k = xmlrpclib.ServerProxy("http://lpnlsst:8087/")

k.connect()
if k.checkConnection() != '6514':
    print >>sys.stderr, "No connection to the photodiode Keithley 6514. Stop."
    sys.exit(2)


k.zeroCorrect()
k.readContinuous(1)

print "Current value ", k.getLastReading()

output = open("map.data", "w")

xyz.move({'z': 0.0})

G = grid.Grid(xmin = 10.0, xmax = 90.0, dx = 10.0,
              ymin = 10.0, ymax = 90.0, dy = 10.0)

for (x,y) in G:
    # x = float(x)
    # y = float(y)
    print "X,Y = ", x,y
    xyz.move({'x': x, 'y': y})
    time.sleep(.5)
    mesure = k.getLastReading()
    print mesure
    print >>output, x,y,mesure

output.close()



