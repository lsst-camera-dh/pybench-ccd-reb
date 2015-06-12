
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

import lsst.testbench.scripts.ccd.functions

print """
CCD output scanning with and without light source.
--------------------

B.ptc_acquisition(explow=0.1, exphigh=2, expdelta=0.1, laserchannel = 2, lasercurrent=45.0)

     Will take a pair of flats with each of the given
     exposure times (plus biases).
     
CCD must be powered up BEFORE running the script

"""

validamps = [2, 3, 4, 5, 6, 11, 12, 13, 14, 15]
serno = '100-00'
eodir = os.path.join('/data/eotest/', serno, 'ptc/ptc-v0/', time.strftime('%Y%m%d'))
if not os.path.isdir(eodir):
    os.makedirs(eodir)

# CCD must be powered up before running the script

# ==============================================================================

def ptc_acquisition(self, explow=0.1, exphigh=2, expdelta=0.1, laserchannel = 2, lasercurrent=45.0):
    """
     Will take a pair of flats with each of the given
     exposure times (plus biases).
    """

    #
    self.laser.select(laserchannel)
    self.laser.setCurrent(laserchannel, lasercurrent)
    self.laser.enable()

    #self.powerup_CCD()
    self.reb.set_testtype('PTC')

    #self.DKD.setup_current_measurements(DKD_range)
    self.PhD.setup_current_measurements(2e-8)

    # Create the logging summary file
    summaryfile = os.path.join(eodir, 'summary.log')
    f = open(summaryfile, 'a')

    print >>f, "# power\t exposure time\t file name"

    effpow = self.laser.getPower(laserchannel)
    # First take bias frames
    self.log("Taking bias")
    m = self.execute_reb_sequence(True, 'ClearBias', 0, 20)
    #to have only useful channels:
    fname = "%s_ptc_bias_%s.fits" % (serno, self.reb.reb.imgtag)
    i = self.conv_to_fits(channels=validamps)
    # to save FITS HDU with headers
    self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

    print >>f, effpow, 0, fname

    for t in np.arange(explow, exphigh+expdelta, expdelta):
        # pair of flats
        for numpair in [1, 2]:
            effpow = self.laser.getPower(laserchannel)
            m = self.execute_reb_sequence(True, 'Acquisition', t)
            #to have only useful channels:
            fname = "%s_ptc_flat%d_%05d_%s.fits" % (serno, numpair, int(t*100), self.reb.reb.imgtag)
            i = self.conv_to_fits(channels=validamps)
            # to save FITS HDU with headers
            self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

            print >>f, effpow, t, fname

    f.close()

    # Shutting down (not the lamp by default)
    self.laser.disable()
    #self.shutdown_CCD()
    # p = self.reb.start_waiting_sequence()

# Attach this method to the Bench class / instance
lsst.testbench.Bench.ptc_acquisition = ptc_acquisition

