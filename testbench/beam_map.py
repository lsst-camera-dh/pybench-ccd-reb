#! /usr/bin/env python

import sys
import time
import datetime

import xmlrpclib

import lsst.instruments.utils.grid as grid


laser = xmlrpclib.ServerProxy("http://lpnlsst:8082")
laser.connect()
lasername = laser.checkConnection()
if "THORLABS" not in lasername:
    print >>sys.stderr, "No connection to the laser. Stop."
    sys.exit(3)

laserchannel = 2
lasercurrent = 45.0


laser.select(0)
laser.disable()
laser.select(laserchannel)
laser.setCurrent(laserchannel, lasercurrent)
laser.enable()
laserpower = laser.getPower(laserchannel)

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

date = datetime.datetime.utcnow().isoformat()

for z in [10.0, 30.0, 50.0, 70.0]:

    filename = "beam-map-%s-%05.2f.data" % (date, z)

    output = open(filename, "w")

    print >>output, "# BEAM MAP"
    print >>output, "# laser channel:", laserchannel
    print >>output, "# laser current:", lasercurrent
    print >>output, "# laser power:", laserpower

    xyz.move({'z': z})

    G = grid.Grid(xmin = 0.0, xmax = 100.0, dx = 10.0,
                  ymin = 0.0, ymax = 100.0, dy = 10.0)

    for (x,y) in G:
        print "target = ", x,y,z
        xyz.move({'x': x, 'y': y})
        print "real position = ", xyz.get_position()
        time.sleep(.5)
        mesure = k.getLastReading()
        print mesure
        print >>output, x, y, z, mesure

    output.close()


laser.disable()

