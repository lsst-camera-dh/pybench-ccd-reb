# ! /usr/bin/env python
#
# LSST
#
# On-line and off-line analysis of CCD images produced on the bench.
# 

import os
import time
import logging
import astropy.io.fits as pyfits
import numpy as np
from lsst.testbench.bench import Bench

B = Bench()  # singleton

B.register('ds9')


def find_channels(hdulist, selectchannels=None):
    """
    Finds which channels actually have data in them. If there is a list of selected channels,
    picks only in that. Returns a list of the EXTNAMEs.
    :type hdulist: pyfits.HDUlist
    :type selectchannels: list
    :return: list
    """
    rangechannel = []

    for ichan in range(48):
        name = "CHAN_%d" % ichan
        if name in hdulist:
            if selectchannels:
                if ichan not in selectchannels:
                    continue
            rangechannel.append(name)

    return rangechannel

def basic_stats(self, hdulist, logtofile=False, selectchannels=None):
    """
    Basic statistics on the frame from the fits HDUlist. 
    Printed to screen and saved to a txt file.
    Appends estimated values to the fits extension header.
    """
    summaryfile = "stats_"+time.strftime("%Y%m%d",time.localtime())+".txt"
    if logtofile:
        logger = open(summaryfile, 'a')

    print("Channel\t MeanLight  SdevLight   MeanOverS   SdevOverS   MeanOverP   SdevOverP")
    for name in find_channels(hdulist, selectchannels):
        hdr = hdulist[name].header
        img = hdulist[name].data
        imgcols = 512
        colstart = 10
        imglines = 2002
        light = img[:imglines, colstart:colstart+imgcols].flatten()
        dark = img[:imglines, colstart+imgcols:].flatten()
        overp = img[imglines+2:, colstart:].flatten()
        
        hdr['AVLIGHT'] = light.mean()
        hdr['STDLIGHT'] = light.std()
        hdr['AVOVERS'] = dark.mean()
        hdr['STDOVERS'] = dark.std()
        hdr['AVOVERP'] = overp.mean()
        hdr['STDOVERP'] = overp.std()
        
        out = "{}\t{:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f}".format(name,
                                                                                 hdr['AVLIGHT'], hdr['STDLIGHT'],
                                                                                 hdr['AVOVERS'], hdr['STDOVERS'],
                                                                                 hdr['AVOVERP'], hdr['STDOVERP'])
        print(out)
        if logtofile:
            logger.write(out+'\n')
    #return out

Bench.basic_stats = basic_stats


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


#TODO: add a rough estimate of gain from a pair of flats
#TODO: rough estimate of the CTE from the first line and first column of overscans

def cut_scan(hdulist, cutcolumns=[180], selectchannels=None):
    """
    Cut and fit plots for images acquired in scanning mode.
    :param cutcolumns: list of columns for display accross column direction
    :param selectchannels: list of selected channels for display (all by default)
    :return:
    """
    values = []
    Nlines = 2000
    Nbins = 256
    lines = np.arange(Nlines)

    for name in find_channels(hdulist, selectchannels):
        #hdr = hdulist[name].header
        img = hdulist[name].data
        chanvalues = []

        # first-order polynomial fit of scans

        polyscan = np.polyfit(lines, img, 1)

        for b in range(Nbins):
            polyfit = np.poly1d(polyscan[:, b])
            residuals = img[:,b] - polyfit(lines)
            chanvalues.append((polyscan[1, b], polyscan[0, b], residuals.std()))
            if b in cutcolumns:
                #TODO: plot along column with fit
        values.append(chanvalues)

    #TODO: log to file, plots along line direction
