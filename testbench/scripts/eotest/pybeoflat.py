# Original: EO test on BNL TS3 bench by Homer Neal
# Port to pybench by Claire Juramy

###############################################################################
# flat
# Acquire flat image pairs for linearity and gain measurement.
# For each 'flat' command a pair of flat field images are acquired
#
# In the configuration file the format for a flat command is
# flat   signal
# where signal is the desired acquired signal level in e-/pixel
#
# FLAT_WL is used to determine what wavelength will be used for illumination
#
###############################################################################

from lsst.testbench.bench import Bench
import eolib

B = Bench()

B.register('PhD')

B.register('cornerstone')

B.register('QTH')

B.register('lakeshore1')

# this registers the REB and BSS
import lsst.testbench.scripts.ccd.functions
# this requires the ccd.functions
import lsst.testbench.scripts.eotest.common

def eoflat(self, acqcfgfile, CCDID):
    """
    Acquire flat image pairs for linearity and gain measurement.
    For each 'flat' command in the config file a pair of flat field images are acquired
    :type self: Bench
    :type acqcfgfile: string
    :type CCDID: string
    :return:
    """
    self.CCDready()

    B.PhD.setup_current_measurements(2e-6)
    #B.PhD.send()  # TODO: to set PLC rate
    nplc = 1

    # see if need to turn off vacuum gauge here too (electronic noise, glow)

    # print "Now collect some parameters from the config file"
    lo_lim = float(eolib.getCfgVal(acqcfgfile, 'FLAT_LOLIM', default='0.1'))
    hi_lim = float(eolib.getCfgVal(acqcfgfile, 'FLAT_HILIM', default='120.0'))
    bcount = float(eolib.getCfgVal(acqcfgfile, 'FLAT_BCOUNT', default = "2"))
    wl     = float(eolib.getCfgVal(acqcfgfile, 'FLAT_WL', default = "550.0"))
    imcount = 2

    seq = 0  # image pair number in sequence

    # set filter here

    ccd = CCDID
    print "Working on CCD %s" % ccd

# go through config file looking for 'flat' instructions, take the flats
    print "Scanning config file for FLAT specifications"
    fp = open(acqcfgfile, "r")
    fpfiles = open("%s/acqfilelist" % cdir,"w")

    owl = 0.
    flux = 0.

    for line in fp:
        tokens = str.split(line)
        if ((len(tokens) > 0) and (tokens[0] == 'flat')):

            target = float(tokens[1])

            print "target exposure = %d" % (target)

#            exptime = eolib.expCheck(calfile, labname, target, wl, hi_lim, lo_lim, test='FLAT', use_nd=False)

# take bias images
            print "set controller for bias exposure"


Bench.eoflat = eoflat

