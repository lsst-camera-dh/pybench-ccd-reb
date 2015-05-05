#! /usr/bin/env python
import sys
import os, os.path
import types
import lsst.testbench
import time
import datetime
import numpy as np

import lsst.testbench

import lsst.instruments.utils.grid as grid

B = lsst.testbench.Bench()

B.register('xyz')
B.register('ttl')
B.register('PhD')

# -----------------------------------------------------------------

print """
metrology/beam_map
--------------------

B.beam_map(self, xmin = 0.0, xmax = 100.0, dx = 5.0,
                 ymin = 0.0, ymax = 100.0, dy = 5.0, 
                 z = 0.0, current_range = 2e-8, n=20, meta = [])

     Will do a map of the incident beam using the PhD photodiode
     (and the connected Keithley). The photodiode should be fixed
     on the XYZ mount.

--------------------

B.laser_beam_map(self, 
                 channels = [1,2,3,4],
                 currents = { 1: 32.0,
                              2: 45.0,
                              3: 55.0,
                              4: 45.0},
                 xmin = 0.0, xmax = 100.0, dx = 5.0,
                 ymin = 0.0, ymax = 100.0, dy = 5.0, 
                 z = 0.0,
                 current_range = 2e-3,
                 n = 20,
                 meta = [])

     Will do a dark map, then a map for each laser channel.


"""

# -----------------------------------------------------------------
def beam_map(self, 
             xmin = 0.0, xmax = 100.0, dx = 5.0,
             ymin = 0.0, ymax = 100.0, dy = 5.0, 
             z = 0.0,
             current_range = 2e-3,
             n = 20,
             meta = []):

    self.log("Homing the XYZ mount (takes up to 3 minutes. Be patient).")
    self.xyz.home(park = False)

    self.log("Setting the Keithley connected to the photodiode")
    self.PhD.setup_current_measurements(current_range)

    self.log("Move to z = %f" % z)
    self.xyz.move({'z': z})

    # Create the data file
    now = datetime.datetime.utcnow()
    datadir = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            now.date().isoformat())

    if not(os.path.isdir(datadir)):
        os.makedirs(datadir)

    datafile = os.path.join(datadir,
                            ("PhD-beam-map-%s.data"
                             % now.isoformat()))
    output = open(datafile, "w")

    if meta != []:
        for line in meta:
            print >>output, "#", line

    print >>output, "# Keithley range = ", current_range
    print >>output, "# "
    print >>output, "# fluxes on the LSST CCD testbench"
    print >>output, "# time\t x\t y\t z\t \t PhD flux\t on/off"

    self.log("Taking dark...")
    self.ttl.closeShutter() # in case

    xyz_pos = self.xyz.position
    xc = xyz_pos['x']
    yc = xyz_pos['y']
    zc = xyz_pos['z']

    for i in xrange(n):
        value = self.PhD.read_measurement()
        print time.time(),xc,yc,zc,value, 0
        print >>output, time.time(),xc,yc,zc,value, 0

    self.log("Opening the shutter")
    self.ttl.openShutter()
    time.sleep(1)

    # Create the optimize Grid

    G = grid.Grid(xmin = xmin, xmax = xmax, dx = dx,
                  ymin = ymin, ymax = ymax, dy = dy)

    for (x,y) in G:
        # x = float(x)
        # y = float(y)
        print "X,Y = ", x,y
        self.xyz.move({'x': x, 'y': y}, wait=True)
        time.sleep(.5)
        for i in xrange(n):
            value = self.PhD.read_measurement()
            print time.time(),x,y,z,value, 1
            print >>output, time.time(),x,y,z,value, 1
        output.flush()

    self.ttl.closeShutter() 
    time.sleep(1)

    self.log("Taking dark...")

    xyz_pos = self.xyz.position
    xc = xyz_pos['x']
    yc = xyz_pos['y']
    zc = xyz_pos['z']

    for i in xrange(n):
        value = self.PhD.read_measurement()
        print time.time(),x,y,z,value, 0
        print >>output, time.time(),x,y,z,value, 0

    output.close()


# B.flux_ramp = types.MethodType(flux_ramp, B)
lsst.testbench.Bench.beam_map = beam_map

# -----------------------------------------------------------------

def laser_beam_map(self, 
                   channels = [1,2,3,4],
                   currents = { 
                       #1: 30.0,
                       1: 35.0,
                       #2: 42.0,
                       2: 45.0,
                       #2: 59.0
                       #2: 60.0,
                       #3: 25.0,
                       #3: 39.0,
                       3: 66.0,
                       #4: 30.0,
                       4: 50.0},
                   xmin = 0.0, xmax = 100.0, dx = 5.0,
                   ymin = 0.0, ymax = 100.0, dy = 5.0, 
                   z = 0.0,
                   current_range = 2e-3,
                   n = 20,
                   meta = []):          

    # First register the laser if not yet done

    self.register("laser")

    # First turn off all the channels, in case
    self.laser.disable()
    for ch in self.laser.allchannels:
        self.laser.unselect(ch)
    time.sleep(2)

    # Dark map

    self.log("First taking a dark map (laser off)")

    self.beam_map(xmin = xmin, xmax = xmax, dx = dx,
                  ymin = ymin, ymax = ymax, dy = dy,	 
                  z = z,
                  current_range = current_range,
                  n = n,
                  meta = ["Dark map (everything off)"])

    for ch in channels:
        self.log("Enable laser channel %d" % ch)
        self.laser.select(ch)
        self.laser.enable()
        time.sleep(2)
        #
        self.log("Setting up the current for channel %d" % ch)
        self.laser.setCurrent(ch, currents[ch])
        
        self.beam_map(xmin = xmin, xmax = xmax, dx = dx,
                      ymin = ymin, ymax = ymax, dy = dy,	 
                      z = z,
                      current_range = current_range,
                      n = n,
                      meta = ["Laser channel = %d" % ch,
                              "Laser current = %f" % currents[ch]])

        self.log("Disable Laser channel %d" % ch)
        self.laser.unselect(ch)
        self.laser.disable()
        time.sleep(2)

lsst.testbench.Bench.laser_beam_map = laser_beam_map

# -----------------------------------------------------------------
