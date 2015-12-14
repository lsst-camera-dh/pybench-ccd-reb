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

# this registers the REB and BSS
import lsst.testbench.scripts.ccd.functions
# this requires the ccd.functions
import lsst.testbench.scripts.eotest.common

B.CCDready()

B.PhD.setup_current_measurements(2e-6)
#B.PhD.send()  # TODO: to set PLC rate

# see if need to turn off vacuum gauge here too (electronic noise, glow)

# print "Now collect some parameters from the config file"
lo_lim = float(eolib.getCfgVal(acqcfgfile, 'FLAT_LOLIM', default='0.1'))
hi_lim = float(eolib.getCfgVal(acqcfgfile, 'FLAT_HILIM', default='120.0'))
bcount = float(eolib.getCfgVal(acqcfgfile, 'FLAT_BCOUNT', default = "2"))
wl     = float(eolib.getCfgVal(acqcfgfile, 'FLAT_WL', default = "550.0"))
imcount = 2

