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
    dataDir = "/home/karkar/fromXPS/LSST/dataTestCCD/20140731/"
    filelist = [dataDir+"0x00020140731000{:0>2d}.fits".format(i) for i in range(45,77)]
    nfile = len(filelist)
    print "nfile" , nfile
    dark = []
    header = []
    imgcols = 512
    colstart = 10
    imglines = 2002
    exptime = np.zeros(nfile)

    fig = plt.figure("Light")
    fig2= plt.figure("Overscan")
    for ifile, filename in enumerate(filelist):
        print "now using file : ", filename
        myfile = pyfits.open(filename)
        exptime[ifile] = myfile[0].header.get("EXPTIME")
        nblocs = len(myfile)
        # print "nblocs = ",nblocs
        mycolors = cycle(get_color(nblocs))
        for ibloc in range(1, nblocs):
            channel = myfile[ibloc].header.get("EXTNAME")
            # print channel, exptime[ifile]
            if ((channel != None) and("CHAN" in channel) and (exptime[ifile] != 0.) ) :
                if firstplot == True :
                     firstplot = False
                     setleg = True
                imgdark =  myfile[ibloc].data
                lightzone = imgdark[:imglines, colstart:colstart+imgcols]
                plt.figure(fig.number)
                plt.plot(exptime[ifile], lightzone.mean(), linewidth = 0., color = next(mycolors), marker = "*", markersize = 10., label = channel)
                over  = imgdark[imglines+2:, colstart:]
                plt.figure(fig2.number)
                plt.plot(exptime[ifile], over.mean(), linewidth = 0.,color = next(mycolors), marker = "d", markersize = 8., label = channel)
        if setleg == True :
            setleg = False
            print "doing the legend"
            plt.figure(fig.number)
            plt.xlim(-20., 520)
            plt.ylim(-70000,-45000)
            plt.legend(loc=10,prop={'size':8})
            plt.grid(True)
            plt.figure(fig2.number)
            plt.xlim(-20., 520)
            plt.ylim(-70000,-45000)
            plt.grid(True)
            plt.legend(loc=10,prop={'size':8})
        myfile.close()
    fig.savefig(dataDir+"./plots/lightVSexpTime.png")
    fig2.savefig(dataDir+"./plots/overscanVSexpTime.png")
    # plt.show()