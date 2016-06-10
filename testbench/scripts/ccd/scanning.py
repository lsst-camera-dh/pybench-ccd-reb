
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

laserchannel = 2
lasercurrent=45.0
serno = '100-00'
eodir = os.path.join('/data/eotest/system/scanning-v0/', time.strftime('%Y%m%d'))
if not os.path.isdir(eodir):
    os.makedirs(eodir)

# CCD must be powered up before running the script

# ==============================================================================

def scanning_frame(self, exptype='Acquisition' , exptime=0.2, tm=True, validamps = None):
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
    self.reb.stop_waiting_sequence()
    self.reb.reb.set_pointer('CleaningNumber', 2)

    # First take normal frames
    for numpair in [1, 2]:
        self.log("Taking reference frame %d for scanning" % numpair)
        m = self.execute_reb_sequence(exptype, exptime)
        fname = "acq_frame%d_%s.fits" % (numpair, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

    self.reb.set_parameter('TM', tm)
    # Then put into scanning mode and change image size
    self.reb.start_adc_increment()

    for numpair in [1, 2]:
        self.log("Taking scanning frame %d" % numpair)
        m = self.execute_reb_sequence(exptype, exptime)
        fname = "acq_scan%d_%s.fits" % (numpair, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps, borders=True)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

    self.reb.stop_adc_increment()
    self.reb.set_parameter('TM', False)
    self.reb.start_waiting_sequence()

    #  TODO: add display from analysis

# Attach this method to the Bench class / instance
lsst.testbench.Bench.scanning_acquisition = scanning_acquisition


def super_scan(self, exptype='Acquisition' , exptime=0.2, tm=True, validamps = None):
    """
    Acquire a super-scan of every pixel of the frame.
    :param self:
    :param exptype:
    :param exptime:
    :param tm:
    :param validamps:
    :return:
    """
    self.reb.set_testtype('SCAN')
    self.reb.stop_waiting_sequence()
    self.reb.reb.set_pointer('CleaningNumber', 2)


