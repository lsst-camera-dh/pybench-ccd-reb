#! /usr/bin/env python
#
# LSST
#
# Simple tools to analyze fits files

import sys
import time
import numpy as np
import pyfits
from matplotlib import pyplot as plt
import colorsys
from itertools import cycle
 
def get_color(color):
    for hue in range(color):
        hue = 1. * hue / color
        col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
        yield "#{0:02x}{1:02x}{2:02x}".format(*col)
       
if __name__ == '__main__':
    firstplot = True
    setleg = False
    filelist = ["/home/karkar/fromXPS/LSST/dataTestCCD/20140731/0x00020140731000{:0>2d}.fits".format(i) for i in range(7,77)]
#    filearray = np.array(filelist)
#    nfile, nblocs = filearray.shape
    nfile = len(filelist)
    print "nfile" , nfile
#    print "nfile, nblocs" , nfile, nblocs
#    mycolors = cycle(get_color(nblocs))
    dark = []
    header = []
    imgcols = 512
    colstart = 10
    imglines = 2002
#    print header.shape
    exptime = np.zeros(nfile)
#    for ifile in range(nfile):
    for ifile, filename in enumerate(filelist):
        myfile = pyfits.open(filename)
        exptime[ifile] = myfile[0].header.get("EXPTIME")
        nblocs = len(myfile)
#        print "nblocs = ",nblocs
        mycolors = cycle(get_color(nblocs))
        for ibloc in range(1, nblocs):
            channel = myfile[ibloc].header.get("EXTNAME")
            if ((channel != None) and("CHAN" in channel) and (exptime[ifile] != 0.) ) :
                if firstplot == True :
                     firstplot = False
                     setleg = True
#                print channel
                imgdark =  myfile[ibloc].data
                lightzone = imgdark[:imglines, colstart:colstart+imgcols]
#                print light.shape
#                over  = imgdark[imglines+2:, colstart:] ## why +2 ?
#                print over.shape
                
                plt.plot(exptime[ifile], lightzone.mean(), linewidth = 0., color = next(mycolors), marker = "*", markersize = 10., label = channel)
#                plt.plot(exptime[ifile], over.mean(), linewidth = 0., marker = "*", markersize = 10., label = channel)
        if setleg == True :
            setleg = False
            plt.legend()
    myfile.close()
                
    plt.show()
#                  print        
#    imgdarks = np.array([file[ibloc].data for ifile in range(nfile) for ibloc in range(nblocs)  for ichan in range(16) if ((myfile[ibloc].header.get("EXTNAME") == "CHAN_%d" % ichan) and (myfile[0].header.get("EXPTIME") != 0.) ) ])
#    print imgdarks.shape
#            dark.append(np.concatenate((img[:imglines, :colstart].flatten(),
#                                   img[:imglines, colstart+imgcols:].flatten(),
#                                   img[imglines:].flatten())))
#    dark = np.array(dark)
#    for ichan in range(16):
#        out = "{}\t{:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f}".format(name,
#                                                                                 light[ichan].mean(), light[ichan].std(),
#                                                                                 dark[ichan].mean(), dark[ichan].std(),
#                                                                                 over[ichan].mean(), over[ichan].std())
#        print(out)
#        logger.write(out+'\n')

    #correlated noise
    #np.corrcoef(x,y)

#    logger.close()
