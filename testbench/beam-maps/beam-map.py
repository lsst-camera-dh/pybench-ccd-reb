#! /usr/bin/env python

import sys
import time
import datetime

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


# k = xmlrpclib.ServerProxy("http://lpnlsst:8087/")
k = xmlrpclib.ServerProxy("http://lpnlsst:8102/")

k.open()
# if k.checkConnection() != '6514':
#     print >>sys.stderr, "No connection to the photodiode Keithley 6514. Stop."
#     sys.exit(2)

if 'KEITHLEY' not in k.get_serial():
    print >>sys.stderr, "No connection to the photodiode Keithley 6514. Stop."
    sys.exit(2)  

k.send("*RST")
k.send("SYST:ZCH ON")

k.send("FUNC 'CURR:DC'")
k.send("CURR:RANG 2e-8")
k.send("SYST:ZCOR ON")
k.send("SYST:ZCH OFF")


# k.zeroCorrect()
# k.readContinuous(1)

# print "Current value ", k.getLastReading()

now = datetime.datetime.utcnow()
z = 0.0

output = open("sphere-map-z=%f-%s.data" % (z, now.isoformat()), "w")

xyz.move({'z': 0.0})

# G = grid.Grid(xmin = 0.0, xmax = 100.0, dx = 10.0,
#               ymin = 0.0, ymax = 100.0, dy = 10.0)

G = grid.Grid(xmin = 90.0, xmax = -10.0, dx = -10.0,
              ymin = 0.0, ymax = 100.0, dy = 10.0)

for (x,y) in G:
    # x = float(x)
    # y = float(y)
    print "X,Y = ", x,y
    xyz.move({'x': x, 'y': y})
    time.sleep(.5)
    # mesure = k.getLastReading()
    s = k.send("READ?")
    elts = s.split(",")
    if len(elts) < 3:
        print >>sys.stderr, "error: no data from the Keithley, stop."
        sys.exit(3)
    mesure = float(elts[0])
    print mesure
    print >>output, x,y,mesure
    output.flush()

output.close()



