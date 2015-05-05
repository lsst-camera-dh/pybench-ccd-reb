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

B = lsst.testbench.bench()

B.register('xyz')
B.register('shutter')
B.register('PhD')

print """
metrology/beam_map
--------------------

B.beam_map(self, outputfile,
                 xmin = 0.0, xmax = 100.0, dx = 5.0,
                 ymin = 0.0, ymax = 100.0, dy = 5.0, 
                 z = 0.0, current_range = 2e-8)

     Will do a map of the incident beam using the PhD photodiode
     (and the connected Keithley). The photodiode should be fixed
     on the XYZ mount.

     The resulting points are written/appended in <outputfile>.
"""

def beam_map(self, 
             outputfile,
             xmin, xmax, dx,
             ymin, ymax, dy, 
             z = 0.0,
             current_range = 2e-8,
             meta = []):

    B.log("Setting the Keithley connected to the photodiode")
    self.PhD.setup_current_measurements(current_range)

    B.log("Opening the shutter")
    self.ttl.openShutter()
    time.sleep(1)

    B.log("Move to z = %f" % z)
    B.xyz.move({'z': z})

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
    f = open(datafile, "w")

    if meta != []:
        for line in meta:
            print >>f, "#", meta

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# time\t x\t y\t z\t \t PhD flux"

    # Create the optimize Grid

    G = grid.Grid(xmin = xmin, xmax = xmax, dx = dx,
                  ymin = ymin, ymax = ymax, dy = dy)

    for (x,y) in G:
        # x = float(x)
        # y = float(y)
        print "X,Y = ", x,y
        xyz.move({'x': x, 'y': y})
        time.sleep(.5)
        # mesure = k.getLastReading()
        value = PhD.
        print >>output, x,y,mesure
        output.flush()

    f.close()

    self.ttl.closeShutter()
    time.sleep(2)

# B.flux_ramp = types.MethodType(flux_ramp, B)
lsst.testbench.Bench.beam_map = beam_map
