#! /usr/bin/env python

import sys
import time
import datetime
import os, os.path
import getopt

import xmlrpclib

import lsst.instruments.utils.grid as grid


option_channel = False
nb_channel = 1
nb_turn = 1

def usage():
    print "Missing argument"

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:t:", ["channel", "turn",])
    
except getopt.GetoptError:
    # print help information and exit
    usage()
    sys.exit(1)
    
for option, arg in opts:
    if option in ("-c", "--channel"):
        #if arg not in [1,2,3,4]:
         #   print "Channel number must be 1, 2, 3 or 4"
          #  sys.exit(1)
        #else:
        option_channel = True
        nb_channel = arg
    if option in ("-t", "--turn"):
        nb_turn = arg


laser = xmlrpclib.ServerProxy("http://lpnlsst:8082")
laser.connect()
lasername = laser.checkConnection()
if "THORLABS" not in lasername:
    print >>sys.stderr, "No connection to the laser. Stop."
    sys.exit(3)

lasercurrents = { 1: 30.0,
                  2: 45.0,
                  3: 25.0,
                  4: 30.0 }

for i in [1,2,3,4]: laser.select(-i)
laser.disable()

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

if option_channel == True:
    laserchannels = [nb_channel]
else:
    laserchannels = [1, 2, 3, 4]

print "Nb of turn in the loop : " + str(nb_turn)

for turn_in_loops in range(nb_turn):

    print "Turn : " + str(turn_in_loop)

    for laserchannel in laserchannels:
        
        k.send("*RST")
        k.send("SYST:ZCH ON")
        
        k.send("FUNC 'CURR:DC'")
        # k.send("CURR:RANG 2e-8")
        k.send("CURR:RANG 2e-8")
        k.send("SYST:ZCOR ON")
        k.send("SYST:ZCH OFF")


        # k.zeroCorrect()
        # k.readContinuous(1)

        # print "Current value ", k.getLastReading()

        now = datetime.datetime.utcnow()
        z = 0.0

        output = open("sphere-map-z=%f-%s.data" % (z, now.isoformat()), "w")

        # measure the dark current

        for i in xrange(20):
            s = k.send("READ?")
            elts = s.split(",")
            if len(elts) < 3:
                print >>sys.stderr, "error: no data from the Keithley, stop."
                sys.exit(3)
            measure = float(elts[0])
            print measure
            print "dark current =", measure
            print >>output, "# dark current =", measure
            output.flush()

        # Turn on the laser

        laser.select(laserchannel)
        lasercurrent = lasercurrents[laserchannel]
        laser.setCurrent(laserchannel, lasercurrent)
        laser.enable()
        print "Waiting for the laser to turn On..."
        time.sleep(7)


        print >>output, "# laser channel = ", laserchannel
        print >>output, "# laser current (mA) = ", lasercurrent
        laserpower = laser.getPower(laserchannel)
        print >>output, "# laser power (mW) = ", laserpower
        print >>output, "# z (mm) = ", z

        xyz.move({'z': z})

        G = grid.Grid(xmin = 0.0, xmax = 100.0, dx = 10.0,
                      ymin = 0.0, ymax = 100.0, dy = 10.0)

        # G = grid.Grid(xmin = 90.0, xmax = -10.0, dx = -10.0,
        #               ymin = 0.0, ymax = 100.0, dy = 10.0)

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
            measure = float(elts[0])
            print measure
            print >>output, x, y, measure
            output.flush()

        # shutdown the laser

        laser.disable()
        for i in [1,2,3,4]: laser.select(-i)
        print "Waiting for the laser to turn Off..."
        time.sleep(2)

        # measure the dark current

        for i in xrange(20):
            s = k.send("READ?")
            elts = s.split(",")
            if len(elts) < 3:
                print >>sys.stderr, "error: no data from the Keithley, stop."
                sys.exit(3)
            measure = float(elts[0])
            print "dark current =", measure
            print >>output, "# dark current =", measure
            output.flush()


        output.close()




