# ! /usr/bin/env python
#
# LSST
#
# On-line and off-line analysis of CCD images produced on the bench.
# 

import os
import time

import numpy as np
from matplotlib import pyplot as plt
import astropy.io.fits as pyfits


# USAGE

#s2 = pyfits.open('/Users/nayman/Documents/REB/REB3/LPNHEtest/20151014/0x0020151014134249.fits')
#s2[0].header['width'] = 256  # if missing from header (older files)
#s2[0].header['height'] = 1000
#s2[0].header['detsize'] = '[1:6144,1:2000]'
#cut_scan_plot(s2)

#h = pyfits.open('/Users/nayman/Documents/REB/REB3/LPNHEtest/xmemory/reb3-ch4-2V-att10.fz')
#outfilename='/Users/nayman/Documents/REB/REB3/LPNHEtest/xmemory/xtalk_memory-db10.txt'
#outfile = open(outfilename,'a')
#xtalk_memory(h, 4, 50000, outfile)
#outfile.close()

# UTILITIES

def open_fits(infilename):
    try :
        fitsfile = pyfits.open(infilename)
        print "Opening file " + infilename
    except :
        raise ValueError("Sorry, unable to open the file: " + infilename)
    return fitsfile


def find_channels(hdulist, selectchannels=None):
    """
    Finds which channels actually have data in them. If there is a list of selected channels,
    picks only in that. Returns a list of the EXTNAMEs.
    :type hdulist: pyfits.HDUlist
    :type selectchannels: list
    :return: list
    """
    rangechannel = []

    for h in hdulist:
        if 'channel' in h.header:
            ichan = h.header['channel']
            if selectchannels:
                if ichan not in selectchannels:
                    continue
            if 'extname' not in h.header:
                h.header['extname'] = 'CHAN_%02d' % ichan
            rangechannel.append(h.header['extname'])

    return rangechannel


def get_image_id(hdulist):
    """
    Defines the image identifier that will be used for output files.
    :rtype: string
    """
    try:
        fitsname = hdulist[0].header['FILENAME']
    except:
        fitsname = 'fits.fz'
    return fitsname[:-3]

def get_fits_dir(datadir):
    """
    Finds all fits file in the directory, returns a list with complete path.
    :param datadir:
    :return:
    """
    listfile = [os.path.join(datadir,f) for f in os.listdir(datadir) if os.path.splitext(f)[1] == '.fz']
    return listfile

# ANALYSIS METHODS

def stats_on_files(listfile, listnum=[], datadir='', selectchannels=None):
    """
    Very basic statistics over a list of fits files. Useful for linearity of REB.
    :param listfile: list of files without path
    :param listnum: list of index to associate to file
    :param datadir: directory location of files
    :param selectchannels:
    :return:
    """
    fname = os.path.join(datadir, 'stats.txt')
    f = open(fname, 'a')
    for num, fitsfile in enumerate(listfile):
        i = open_fits(os.path.join(datadir, fitsfile))
        if listnum:
            f.write(listnum[num] + '\t')
        else:
            f.write(fitsfile + '\t')
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


def cut_scan_plot(hdulist, cutcolumns=[180], selectchannels=None, outputdir = '', polynomfit=True):
    """
    Cut and fit plots accross image (designed for images acquired in scanning mode).
    If polynomfit is set to False, reverts to average and standard deviation.
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

        if polynomfit:
            stddev = np.empty(Nbins)
            # first-order polynomial fit of scans, plus dispersion
            polyscan = np.polyfit(lines, img, 1)

            for b in range(Nbins):
                polyfit = np.poly1d(polyscan[:, b])
                residuals = img[:,b] - polyfit(lines)
                stddev[b] = residuals.std()
                chanvalues.append((polyscan[1, b], polyscan[0, b], stddev[b]))
                if b in cutcolumns:
                    plt.figure(figY.number)
                    plt.plot(img[:,b])
                    plt.plot(polyfit(lines))

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

        else:
            # mean and standard deviation
            stddev = np.empty(Nbins)
            meanbin = np.empty(Nbins)
            for b in range(Nbins):
                meanbin[b] =  img[:,b].mean()
                stddev[b] = img[:,b].std()
                chanvalues.append((meanbin[b], stddev[b]))
                if b in cutcolumns:
                    plt.figure(figY.number)
                    plt.plot(img[:,b])
                    plt.plot(np.full_like(img[:,b], meanbin[b]))

            # plots along line direction
            plt.figure(figX.number)
            plt.subplot(311)
            plt.plot(meanbin)
            plt.ylabel('Average of column')
            plt.subplot(312)
            plt.plot(stddev)
            plt.ylabel('Dispersion along column')

        values.append(chanvalues)


    # log to file
    rootname = get_image_id(hdulist)
    valuelog = os.path.join(outputdir, 'scanfit' + rootname + '.txt')
    outfile = open(valuelog, 'w')
    # header line
    outfile.write("ScanBin\t")
    for name in listchan:
        if polynomfit:
            outfile.write("%s_P0\t%s_P1\t%s_SD\t" % (name, name, name))
        else:
            outfile.write("%s_MN\t%s_SD\t" % (name, name))
    outfile.write("\n")
    # one line per bin
    for b in range(Nbins):
        outfile.write("%d\t" % b)
        for j in range(len(listchan)):
            if polynomfit:
                outfile.write("%.2f\t%.4f\t%.2f\t" % values[j][b])
            else:
                outfile.write("%.2f\t%.2f\t" % values[j][b])
        outfile.write("\n")

    outfile.close()

    # save figures
    figX.savefig(os.path.join(outputdir, 'scanfit' + rootname + '.png'))
    figY.savefig(os.path.join(outputdir, 'plotscanfit' + rootname + '.png'))

    plt.show()


def deinterlace_scan(Nbins, filename, doplot=True):
    """
    Situation-specific: deinterlaces scan fit results.
    :param Nbins:
    :return:
    """
    scanfile = open(filename, 'r')
    scanlines = scanfile.readlines()
    scanfile.close()
    newname = filename[:-4]+'-deinter.txt'
    newfile = open(newname, 'w')
    newfile.write(scanlines[0])

    rebin = len(scanlines)/Nbins
    for r in range(Nbins):
        for s in range(rebin):
            newfile.write(scanlines[r + 1 + s * Nbins])
    newfile.close()

    # plots
    if doplot:
        data = np.loadtxt(newname, skiprows=1)
        p0b = np.mean(data[:, 1:25:3], axis=1)
        p1b = np.mean(data[:, 2:26:3], axis=1)
        sb = np.mean(data[:, 3:27:3], axis=1)
        p0t = np.mean(data[:, 25::3], axis=1)
        p1t = np.mean(data[:, 26::3], axis=1)
        st = np.mean(data[:, 27::3], axis=1)


        figX, (p0, p1, pdev) = plt.subplots(nrows=3, num='Fit over lines', figsize=(8,12))
        plt.xlabel('Scan increment (10 ns)')
        # plots along line direction
        plt.figure(figX.number)
        plt.subplot(311)
        plt.plot(p0t)
        plt.plot(p0b)
        plt.ylabel('Constant in polynomial fit')
        plt.subplot(312)
        plt.plot(p1t)
        plt.plot(p1b)
        plt.ylabel('Slope in polynomial fit')
        plt.subplot(313)
        plt.plot(st)
        plt.plot(sb)
        plt.ylabel('Residuals from fit')

        figX.savefig(newname[:-4]+'.png')
        plt.show()


def xtalk_memory(hdulist, sourcechan, trigger, outfile, selectchannels=None):
    """
    Calculates crosstalk and memory from one channel with signal to all others.
    :param sourcechan: channel with signal
    :param trigger: minimal level of signal
    :return:
    """

    # can remove first line here (shifted by triggers during warm-up before acquisition)
    source = hdulist["CHAN_%d" % sourcechan].data[1:, :]
    #old : flatten
    #- Skip missing channels:
    if source == [] :
        raise ValueError("Channel %d has no data" % sourcechan)

    #Find indexes of peaks resulting from input pulses
    SplitPeaks = source>trigger

    # if no peak found
    if not np.any(SplitPeaks):
        raise ValueError("No input pulses above %f in channel %d" % (trigger, sourcechan))
    else :
        print "Found %d pulses in channel %d" % (np.count_nonzero(SplitPeaks), sourcechan)

    # baseline for source: find last points before series of peaks
    # number of bins: search for pre_peak_index on first line
    pre_peak_index = np.flatnonzero(np.logical_and(np.logical_not(SplitPeaks[0, :-1]), SplitPeaks[0, 1:]))
    try:
        interval = pre_peak_index[1] - pre_peak_index[0]
        print('Binning over %d pixels' % interval)
    except:
        raise ValueError('Could not find interval between pulses')
    # detect pre_peak on all lines after removing last block of each line (it could be incomplete)
    pre_peak_index = np.nonzero(np.logical_and(np.logical_not(SplitPeaks[:, :-interval-1]), SplitPeaks[:, 1:-interval]))
    # note: pre_peak_index is a tuple of two arrays

    # outputs full memory/crosstalk matrix
    for name in find_channels(hdulist, selectchannels):
        # remove same as source
        receiver = hdulist[name].data[1:, :]

        basereceiver = receiver[pre_peak_index].mean()
        noisereceiver = receiver[pre_peak_index].std()
        #print basereceiver, noisereceiver

        # Split by bins, one line per channel
        outfile.write("%s\t %.2f\t %.2f\t" % (name, basereceiver, noisereceiver))

        for b in range(1, interval):
            value = receiver[(pre_peak_index[0], pre_peak_index[1] + b)].mean() - basereceiver
            outfile.write("%.2f\t" % value)
        outfile.write("\n")


def xmemory_on_files(datadir, outname, sourcechan=None):
    """
    Applies xtalk_memory over all files in a directory (offline version of linearity_scan in scripts.ccd.reb)
    :return:
    """
    listfile = get_fits_dir(datadir)
    outf = open(outname, 'w')
    outf.write('dB\tVoltPre\tVoltPost\tVolt0\tVolt127\n')

    for f in listfile:
        i = pyfits.open(f)
        att = i[0].header['ATT']
        k1 = i[0].header['VOLT1']
        k2 = i[0].header['VOLT2']
        k127 = i[0].header['VOLTBASE']
        k0 = i[0].header['ATT0']

        outf.write('%d\t%f\t%f\t%f\t%f\t' % (att, k1, k2, k0, k127))
        if sourcechan is None:
            for name in find_channels(i):
                img = i[name].data
                light = img[500:, 20:]
                outf.write('%10.2f\t%4.2f\t' % (light.mean(), light.std()))
            outf.write('\n')
        else:
            outf.write('\n')
            try:
                xtalk_memory(i, sourcechan, 35000, outf)
            except:
                outf.write('\n')
        i.close()

    outf.close()

#TODO: add a rough estimate of gain from a pair of flats
#TODO: rough estimate of the CTE from the first line and first column of overscans

