
import os
import lsst.testbench
import time
import numpy as np

B = lsst.testbench.Bench()

B.register('laser')
B.register('lakeshore1')
#B.register("DKD")
# done in ccd.functions:
#B.register("PhD")
#B.register('reb')  # connect to the REB
#B.register('bss')  # connect (remotely) to the BackSubstrate Power

#this should be done in higher level script
#import lsst.testbench.scripts.ccd.functions
B.PhD.setup_current_measurements(2e-8)


print """
Acquisition sequence for CCD output scanning with REB3/WREB.
--------------------
     
B.scanning_acquisition(waittime=4, exptime=0.2, laserchannel = 2, lasercurrent=45.0)

CCD must be powered up BEFORE running the script

"""

validamps = [2, 3, 4, 5, 6, 11, 12, 13, 14, 15]
serno = '100-00'
eodir = os.path.join('/data/eotest/system/scanning-v0/', time.strftime('%Y%m%d'))
if not os.path.isdir(eodir):
    os.makedirs(eodir)

# CCD must be powered up before running the script

# ==============================================================================

def scanning_acquisition(self, waittime=4 , exptime=0.2, laserchannel = 2, lasercurrent=45.0):
    """
     Will take two pairs of exposures as defined, one pair in scanning mode and one pair in normal mode.
    """

    if exptime>0:
        self.laser.select(laserchannel)
        self.laser.setCurrent(laserchannel, lasercurrent)
        self.laser.enable()
    else:
        self.laser.disable()

    self.reb.set_testtype('SCAN')

    # First take normal frames
    for numpair in [1, 2]:
        self.log("Taking reference frame %d for scanning" % numpair)
        m = self.execute_reb_sequence('Acquisition', exptime, waittime)
        fname = "acq_frame%d_%s.fits" % (numpair, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

    # Then put into scanning mode and change image size
    self.reb.start_adc_increment()

    for numpair in [1, 2]:
        self.log("Taking scanning frame %d" % numpair)
        m = self.execute_reb_sequence('Window', exptime, waittime)
        fname = "acq_scan%d_%s.fits" % (numpair, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps, borders=True)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))
    self.reb.stop_adc_increment()


    # p = self.reb.start_waiting_sequence()

# Attach this method to the Bench class / instance
lsst.testbench.Bench.scanning_acquisition = scanning_acquisition

# TODO: use new sequencer to be able to do the scanning on any type of acquisition by changing the window size