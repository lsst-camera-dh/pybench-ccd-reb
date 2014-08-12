#! /usr/bin/env python
#
# LSST
#
# Simple tools to analyze fits files

import sys
import time
import numpy as np
import pyfits


if __name__ == '__main__':

    fitsfile = sys.argv[1]
    hdulist = pyfits.open(fitsfile)
    logfile = "log"+time.strftime("%Y%m%d",time.localtime())+".txt"
    logger = open(logfile, 'a')
    logger.write(fitsfile+'\n')
    light = []
    dark = []
    over = []
    print("Channel\t MeanLight  SdevLight   MeanDark   SdevDark   MeanOver   SdevOver")
    for ichan in range(16):
        name = "CHAN_%d" % ichan
        header = hdulist[name].header
        img = hdulist[name].data
        imgcols = 512
        colstart = 10
        imglines = 2002
        light.append(img[:imglines, colstart:colstart+imgcols])
        dark.append(np.concatenate((img[:imglines, :colstart].flatten(),
                               img[:imglines, colstart+imgcols:].flatten(),
                               img[imglines:].flatten())))
        over.append(img[imglines+2:, colstart:]) ## why +2 ?
    light = np.array(light)
    dark = np.array(dark)
    over = np.array(over)
    for ichan in range(16):
        out = "{}\t{:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f}".format(name,
                                                                                 light[ichan].mean(), light[ichan].std(),
                                                                                 dark[ichan].mean(), dark[ichan].std(),
                                                                                 over[ichan].mean(), over[ichan].std())
        print(out)
        logger.write(out+'\n')

    #correlated noise
    #np.corrcoef(x,y)

    logger.close()
    hdulist.close()
