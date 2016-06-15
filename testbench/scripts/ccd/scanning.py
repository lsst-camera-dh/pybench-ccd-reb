
import os
import lsst.testbench
import time
import numpy as np
from matplotlib import pyplot as plt

import lsst.testbench.scripts.ccd.analysis as analysis

B = lsst.testbench.Bench()

B.register('laser')
B.register('lakeshore1')
B.register('ds9')
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
        self.ds9.load_hdulist(i)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

    self.reb.set_parameter('TM', tm)
    # Then put into scanning mode and change image size
    self.reb.start_adc_increment()

    for numpair in [1, 2]:
        self.log("Taking scanning frame %d" % numpair)
        m = self.execute_reb_sequence(exptype, exptime)
        fname = "acq_scan%d_%s.fits" % (numpair, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps, borders=True)
        self.ds9.load_hdulist(i)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))
        if numpair == 2:
            # polynomial fit along columns, display results
            analysis.cut_scan_plot(i, outputdir=eodir)

    self.reb.stop_adc_increment()
    self.reb.set_parameter('TM', False)
    self.reb.start_waiting_sequence()


# Attach this method to the Bench class / instance
lsst.testbench.Bench.scanning_frame = scanning_frame

# TODO: line plot with TM / non-TM superimposed

def super_scan(self, tm=True, scanpoints=None, validamps = None):
    """
    Acquire a super-scan: timing scan at every pixel of the frame.
    Suggestion: select points in the timing with scanpoints and/or select a small window size.
    Assumes the type of acquisition and exposure time have been set before.
    :param self:
    :param exptype:
    :param exptime:
    :param tm:
    :param validamps:
    :return:
    """
    self.reb.set_testtype('SUPERSCAN')
    self.reb.stop_waiting_sequence()
    self.reb.set_parameter('TM', tm)

    if scanpoints is None:
        scaniter = xrange(0, 200, 10)  # to be changed if pixel read time is higher
        niter = 19
    else:
        scaniter = scanpoints
        niter = len(scanpoints)

    if validamps is None:
        nchan = 16
    else:
        nchan = len(validamps)

    # prepares stacks: lines, columns, and whole window
    cols, lines = self.reb.get_amplifier_size()
    avframe = np.empty((nchan, niter))
    avcols = np.empty((nchan, niter, lines))
    avlines = np.empty((nchan, niter, cols))

    for iterscan, offset in enumerate(scaniter):
        # writes offset value but does not activate increment on ADC
        self.reb.write(0x330001, offset & 0xff, check=False)
        m = self.execute_reb_sequence()
        fname = "scantime_%d_%s.fits" % (offset, self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps, borders=True, cleanup=True)
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

        #stacks in arrays
        for chan in range(nchan):
            avframe[chan, iterscan] = i[chan+1].data.mean()
            avcols[chan, iterscan] = i[chan+1].data.mean(axis=0)
            avlines[chan, iterscan] = i[chan+1].data.mean(axis=1)

    self.reb.set_parameter('TM', False)
    self.reb.start_waiting_sequence()

    # save stacks
    outfile = open(os.path.join(eodir,'stack-superscan-%s.txt' % time.strftime('%H%M%S')))

    for c in range(nchan):
        outfile.write("Frame average channel %d\t" % c)
        for j in range(niter):
            outfile.write("%d\t%.3f\n" % (j, avframe[c, j]))
        outfile.write("\n")

    outfile.close()

    # plots
    plt.figure(figsize=(8,5))
    plt.xlabel('Scan increment (10 ns)')
    plt.ylabel('Average over frame')
    for chan in range(nchan):
        plt.plot(avframe[nchan, :])

    plt.figure(figsize=(8,5))
    plt.xlabel('Scan increment (10 ns)')
    plt.ylabel('Average over column')
    for chan in range(nchan):
        for c in range(cols):
            plt.plot(avlines[nchan, :, c])

    plt.show()



