# ! /usr/bin/env python
#
# LSST
#
# On-line and off-line analysis of CCD images produced on the bench.
#

from lsst.testbench.bench import Bench

B = Bench()  # singleton

B.register('ds9')

# USAGE

#from lsst.testbench.bench import Bench
#B = Bench()
#import lsst.testbench.scripts.ccd.analysis

# from file:
#B.display_file('/Users/nayman/Documents/LSST-CCD/Setups/REB1-new/100-00_ptc_flat_00010_2_20150601155652.fits')

# from HDUlist:
#import astropy.io.fits as pyfits
#s2 = pyfits.open('/Users/nayman/Documents/REB/REB3/LPNHEtest/20151014/0x0020151014134249.fits')
#s2[0].header['width'] = 256
#s2[0].header['height'] = 1000
#s2[0].header['detsize'] = '[1:6144,1:2000]'
#B.display_hdu(s2)

# WRAPPERS

def display_array(self, nparray):

    self.ds9.load_array(nparray)
    self.ds9.set_crosshair(100, 100)
    self.ds9.scale('minmax')

Bench.display_array = display_array


def display_hdu(self, hdulist):

    self.ds9.load_hdulist(hdulist)
    self.ds9.set_crosshair(100, 100)
    self.ds9.scale('minmax')

Bench.display_hdu = display_hdu


def display_file(self, fitsfile):

    self.ds9.load_file(fitsfile)
    self.ds9.set_crosshair(100, 100)
    self.ds9.scale('minmax')

Bench.display_file = display_file

