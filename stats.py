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
    logger.write(fitsfile)

    for ichan in range(1,17):
        hdulist.


    logger.close()
    hdulist.close()