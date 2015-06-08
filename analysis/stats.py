#! /usr/bin/env python
#
# LSST
#
# Simple tools to analyze fits files

import sys
import time
import numpy as np
import pyfits


def basic_stats(hdulist):
    out = ''
    for ichan in range(16):
        name = "CHAN_%d" % ichan
        try:
            img = hdulist[name].data
        except:
            continue
        imgcols = 512
        colstart = 10
        imglines = 2002
        light = img[:imglines, colstart:colstart+imgcols].flatten()
        dark = np.concatenate((img[:imglines, :colstart].flatten(),
                               img[:imglines, colstart+imgcols:].flatten(),
                              img[imglines:].flatten()))
        over = img[imglines+2:, colstart:] ## why +2 ?
        out.join("{}\t{:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f}\n".format(name,
                                                                                 light.mean(), light.std(),
                                                                                 dark.mean(), dark.std(),
                                                                                 over.mean(), over.std()))

    return out


if __name__ == '__main__':

    fitsfile = sys.argv[1]
    hdulist = pyfits.open(fitsfile)
    logfile = "log"+time.strftime("%Y%m%d",time.localtime())+".txt"
    logger = open(logfile, 'a')
    logger.write(fitsfile+'\n')

    print("Channel\t MeanLight  SdevLight   MeanDark   SdevDark   MeanOver   SdevOver")
    out = basic_stats(hdulist)
    print(out)
    logger.write(out)

    #correlated noise
    #np.corrcoef(x,y)

    logger.close()
    hdulist.close()
