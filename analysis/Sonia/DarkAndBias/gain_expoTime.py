#! /usr/bin/env python

import numpy as np
import pyfits
import matplotlib as mpl
from matplotlib import pyplot as plt
from utils import get_color, CreateFig
from utils.fitting import *
from itertools import cycle
       
firstplot = True
setleg = False
dataDir = "/home/karkar/fromXPS/LSST/data/dataTestCCD/20140806/"
dataDir2 = "/home/karkar/fromXPS/LSST/data/dataTestCCD/20140807/"
allsets = []
#laser fiber in front of the CCD (distance ~30 cm)
#  laser 635 nm I_laser = 40 (mA ?)  P_laser = 0.06 - 0.07 mW (not that stable)
#
#  Increasing exposure times (2 series)
allsets.append(( "laser635_I40mA", [dataDir+"0x00020140806000{:0>2d}.fits".format(i) for i in range(28,66)]))#66
#Increasing the laser power, same config
#  635 nm  I_laser = 45 (mA ?)  P_laser = 0.72 mW (fluctuations)
#  exposure time from 0.001 (same caveat) to 0.1
allsets.append( ("laser635_I45mA",[dataDir+"0x00020140806000{:0>2d}.fits".format(i) for i in range(87,93)]))
#changing the laser power, same config
#  635 nm  I_laser = 43 (mA ?)  P_laser = 0.43 mW (fluctuations)
#  different exposure times
allsets.append(( "laser635_I43mA", [dataDir+"0x0002014080600{:0>3d}.fits".format(i) for i in range(93,102)]))
#different laser diode : 406 nm
#  I_laser = 16 (mA ?)  P_laser = 0.06 mW (fluctuations)
#  no flux.
allsets.append( ("laser406_I16mA",[dataDir+"0x0002014080600{:0>3d}.fits".format(i) for i in range(102,105)]))
#different laser diode : 406 nm
#  I_laser = 26 (mA ?)  P_laser = 1.39 mW (fluctuations)
allsets.append( ("laser406_I26mA", [dataDir+"0x0002014080600{:0>3d}.fits".format(i) for i in range(116,127)]))
#we decide to vary the laser current.
#  lambda = 635 nm
#  same optical setup
#  see file 'laser-power-635.data'
#allsets.append( ("laser635_variousI",[dataDir+"0x0002014080600{:0>3d}.fits".format(i) for i in range(126,142)]))

#4 images have been taken with the red laser sent into the integrating sphere.
#various exposure times.
#allsets.append( ("laser635_integratingSphere", [dataDir2+"0x0002014080700{:0>3d}.fits".format(i) for i in range(142,147)]))


badfillist = [dataDir+"0x0002014080600023.fits", dataDir+"0x0002014080600066.fits"]

filelistname, filelist  = allsets[0]
nfile = len(filelist)
print "using filelist", filelistname ,"with ", nfile, "files"
dark = []
header = []
imgcols = 512
colstart = 10
imglines = 2002
exptime = np.zeros(nfile)
nchannel = 16
figlist, gslist = CreateFig(r'$\sigma^{2}_{im_{2}-im_{1}}= a+ b.\mu_{im_{2}+im_{1}} + c.\mu_{im_{2}+im_{1}}^2$',nchannel,sizeX=24.,sizeY=16.,)
fig = figlist[0]
gs = gslist[0]
ax = []
def line(x): return slope()*x + offset()
def poly2(x): return a() +b()*x + c()*x*x
for chan in range(16):
    ax.append(plt.subplot(gs[chan/4, chan%4]))
#figlist2, gslist2 = CreateFig("Overscan",nchannel,sizeX=20.,sizeY=16.,)
#fig2 = figlist2[0]
#gs2 = gslist2[0]
#ax2 = []
#for chan in range(16):
#    ax2.append(plt.subplot(gs[chan/4, chan%4]))
mycolors = cycle(get_color(nfile))
X = -1*np.ones((nchannel,nfile/2))
Y = -1*np.ones((nchannel,nfile/2))

for index, filename in enumerate(filelist[::2]):
    ifile = 2*index
    print ifile
    if filename in badfillist or filelist[ifile+1]in badfillist:
        print "skipping files :", filename, filelist[ifile+1]
        continue
    print "now using files : ", filename[len(dataDir):], (filelist[ifile+1])[len(dataDir):]
    myfile = pyfits.open(filename)
    myfile2 = pyfits.open(filelist[ifile+1])
    
    exptime[ifile] = myfile[0].header.get("EXPTIME")
    exptime[ifile+1] = myfile2[0].header.get("EXPTIME")
    if exptime[ifile] < 0.015:
        print "skipping files  ", filename[len(dataDir):], (filelist[ifile+1])[len(dataDir):], "with too small exposure time: ",  exptime[ifile], exptime[ifile+1]
        continue
    if exptime[ifile] != exptime[ifile+1]:
        print "error the two files ", filename[len(dataDir):], (filelist[ifile+1])[len(dataDir):], "don't have the same exposure time"
        print exptime[ifile], "and", exptime[ifile+1]
    thiscolor = next(mycolors)
    nblocs = len(myfile)
    # print "nblocs = ",nblocs
    for ibloc in range(1, nblocs):
        channel = myfile[ibloc].header.get("EXTNAME")
        # print channel, exptime[ifile]
        if ((channel != None) and("CHAN" in channel) and (exptime[ifile] != 0.) ) :
            chan = int(channel[len("CHAN_"):])
#            print chan
            img =  myfile[ibloc].data
            lightzone = img[:imglines, colstart:colstart+imgcols]
            over  = img[imglines+2:, colstart:]
            img2 =  myfile2[ibloc].data
            lightzone2 = img2[:imglines, colstart:colstart+imgcols]
            over2  = img2[imglines+2:, colstart:]
            lightmean = np.mean(lightzone+lightzone2) - np.mean(over+over2)
            lightvar = np.var(lightzone-lightzone2)
            X[chan][index] =  lightmean
            Y[chan][index] = lightvar
            
    myfile.close()

for chan in range(16):
#    remove -1 the values which are left from the array creation (if some file were not used)
    plotx = np.delete(X[chan],np.where(X[chan]==-1))
    ploty = np.delete(Y[chan],np.where(X[chan]==-1))
    exptimeplot = np.delete(exptime[::2], np.where(X[chan]==-1))
#   Plot the data
    plot = ax[chan].scatter(plotx,ploty,  linewidth = 0., c= exptimeplot, cmap=mpl.cm.rainbow,  marker = "*", s= 350)
    #  Fit a line per channel
#    slope = Parameter(1.)
#    offset = Parameter(1.)
#    fit(line,[slope,offset],ploty,plotx)
#    print slope.__call__(), offset.__call__()
#Fit a 2nd degree polynom
    a  = Parameter(1.)
    b  = Parameter(1.)
    c  = Parameter(1.)
    fit(poly2,[a,b,c],ploty,plotx) 
    print a.__call__(), b.__call__(), c.__call__()
    plt.figure(fig.number)
#    #         Plot the line fitted
    continuousX = np.linspace(plotx.min(),plotx.max(),5000)
    ax[chan].plot(continuousX,[poly2(x) for x in continuousX],'--', marker = 'None')
    fitlabel = "a = {:.3g}\nb = {:.3g}\nc = {:.3g}".format(a.__call__(),b.__call__(), c.__call__() )
    ax[chan].text(0.07,0.65,fitlabel, transform=ax[chan].transAxes)
    ax[chan].set_title("Channel {}".format(chan))
    ax[chan].ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
    ax[chan].ticklabel_format(axis='y', style='sci', scilimits=(-2,4))
gs.update(left=0.05,right= 0.85, top=0.90, bottom = 0.05, wspace=0.25,hspace=0.3)    
#fig.subplots_adjust(right=0.8)
cbar_ax = fig.add_axes([0.9, 0.08, 0.02, 0.8])
cbar =fig.colorbar(plot, cax=cbar_ax)

cbar_ax.set_xlabel("\n Exposure time \n in seconds")
fig.savefig(dataDir+"./plots/light_vardiffVSsum_{}.png".format(filelistname))
