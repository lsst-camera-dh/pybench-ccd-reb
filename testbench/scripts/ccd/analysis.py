# ! /usr/bin/env python
#
# LSST
#
# On-line and off-line analysis of CCD images produced on the bench.
# 

import os
import time
import logging

import numpy as np
from matplotlib import pyplot as plt
import astropy.io.fits as pyfits
#from lsst.testbench.drivers.ds9display import split_slicing

from lsst.testbench.bench import Bench

dataDir = './'

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
#B.cut_scan_plot(s2)


# UTILITIES


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


def get_image_id(hdulist):
    """
    Defines the image identifier that will be used for output files.
    :rtype: string
    """
    fitsname = hdulist[0].header['FILENAME']
    return fitsname[:-3]


# ANALYSIS METHODS

def stats_on_files(listfile, listnum, datadir, selectchannels=None):
    """
    Very basic statistics over a list of fits files. Useful for linearity of REB.
    :param listfile: list of files without path
    :param listnum: list of index to associate to file
    :param datadir: directory location of files
    :param selectchannels:
    :return:
    """
    fname = datadir + 'stats.txt'
    f = open(fname)
    for num,fitsfile in enumerate(listfile):
        i = pyfits.open(os.path.join(datadir,fitsfile))
        f.write(listnum[]+'\t')
        for name in find_channels(i, selectchannels):
            img = i[name].data
            light = img[500:, 20:]
            f.write('%10.2f\t%4.2f\t' % (light.mean(), light.std()))
        i.close()
        f.write('\n')
    f.close()
    print('Wrote stats for list to %s' % fname)


def area_stats(hdulist, logtofile=False, selectchannels=None):
    """
    Basic statistics on the frame from the fits HDUlist, split into ligth and dark areas.
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


def cut_scan_plot(hdulist, cutcolumns=[180], selectchannels=None):
    """
    Cut and fit plots accross image (designed for images acquired in scanning mode).
    :param cutcolumns: list of columns for display accross column direction
    :param selectchannels: list of selected channels for display (all by default)
    :return:
    """
    values = []
    figX, (p0, p1, pdev) = plt.subplots(nrows=3, num='Fit over lines', figsize=(8,12))
    plt.xlabel('Scan increment (10 ns)')
    figY = plt.figure(num='Selected line fit', figsize=(8,5))
    plt.xlabel('Line')
    plt.ylabel('ADU')

    Nlines = hdulist[0].header['HEIGHT']
    Nbins = hdulist[0].header['WIDTH']
    lines = np.arange(Nlines)

    listchan = find_channels(hdulist, selectchannels)
    for name in listchan:
        #hdr = hdulist[name].header
        img = hdulist[name].data
        #dsec = split_slicing(hdr['DATASEC'])
        #Nbins = dsec[1]
        #Nlines = dsec[3]

        chanvalues = []

        # first-order polynomial fit of scans

        polyscan = np.polyfit(lines, img, 1)
        stddev = np.empty(Nbins)
        for b in range(Nbins):
            polyfit = np.poly1d(polyscan[:, b])
            residuals = img[:,b] - polyfit(lines)
            stddev[b] = residuals.std()
            chanvalues.append((polyscan[1, b], polyscan[0, b], stddev[b]))
            if b in cutcolumns:
                plt.figure(figY.number)
                plt.plot(img[:,b])
                plt.plot(polyfit(lines))
        values.append(chanvalues)

        # plots along line direction
        plt.figure(figX.number)
        #p0.plot(polyscan[1, :])
        plt.subplot(311)
        plt.plot(polyscan[1, :])
        plt.ylabel('Constant in polynomial fit')
        plt.subplot(312)
        plt.plot(polyscan[0, :])
        #p1.plot(polyscan[0, :])
        plt.ylabel('Slope in polynomial fit')
        plt.subplot(313)
        plt.plot(stddev)
        #pdev.plot(stddev)
        plt.ylabel('Residuals from fit')

    # log to file
    rootname = get_image_id(hdulist)
    valuelog = os.path.join(dataDir, 'scanfit' + rootname + '.txt')
    outfile = open(valuelog, 'w')
    # header line
    outfile.write("ScanBin\t")
    for name in listchan:
        outfile.write("%s_P0\t%s_P1\t%s_SD\t" % (name, name, name))
    outfile.write("\n")
    # one line per bin
    for b in range(Nbins):
        outfile.write("%d\t" % b)
        for j in range(len(listchan)):
            outfile.write("%.2f\t%.4f\t%.2f\t" % values[j][b])
        outfile.write("\n")

    outfile.close()

    # save figures
    figX.savefig(os.path.join(dataDir, 'scanfit' + rootname + '.png'))
    figY.savefig(os.path.join(dataDir, 'plotscanfit' + rootname + '.png'))

    plt.show()


#TODO: add a rough estimate of gain from a pair of flats
#TODO: rough estimate of the CTE from the first line and first column of overscans
