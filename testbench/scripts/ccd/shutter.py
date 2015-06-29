# ! /usr/bin/env python
#
# LSST
#
# Calibration of the shutter exposure time
# based on the CLAP
# 

import os
import time
import logging
import astropy.io.fits as pyfits

#reload(lsst.testbench.scripts.ccd.functions)

import lsst.testbench.bench as bench

B = bench.Bench()  # singleton

# B.register('reb')  # connect to the REB
# B.register('bss')  # connect (remotely) to the BackSubstrate Power

B.load("ccd.functions")

B.register('CLAP')

B.register('laser')

def calibrate_shutter(self):
    """
    Data acquisition to calibrate the exposure time with the CLAP.
    """

    B.laser.select(2)

    # for current in [0.0, 10.0, 20.0, 30.0, 40.0, 42.0, 45.0, 50.0]:
    for current in [42.0, 44.0, 46.0]:
        B.log("Set laser current to %f on channel 2..." % current)
        B.laser.setCurrent(2, current)
        B.laser.enable()
        time.sleep(2)

        for exptime in [0.01, 0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 
                        1., 2., 3., 4., 5., 6., 7., 8., 9., 10.]:
            for i in xrange(5):
                meta = B.execute_reb_sequence('Acquisition', exptime=exptime)
                img = B.conv_to_fits()
                B.save_to_fits(img, meta)

        B.laser.disable()
        time.sleep(2)


# Graft the method on the Bench singleton class
bench.Bench.calibrate_shutter = calibrate_shutter



