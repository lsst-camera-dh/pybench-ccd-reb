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
allsets = []
#we decide to vary the laser current.
#  lambda = 635 nm
#  same optical setup
#  see file 'laser-power-635.data'
allsets.append( ("laser635_variousI",[dataDir+"0x0002014080600{:0>3d}.fits".format(i) for i in range(130,142)]))
laserpower = np.array([0.07, 0.25, 0.42, 0.57, 0.72, 0.88])

badfillist = []

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

#mycolors = cycle(get_color(nfile))
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
#    thiscolor = next(mycolors)
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
#            over  = img[imglines+2:, colstart:]
            img2 =  myfile2[ibloc].data
            dark = img2[:imglines, colstart:colstart+imgcols]
#            over2  = img2[imglines+2:, colstart:]
            lightmean = np.mean(lightzone-dark)
            lightvar = np.var(lightzone-dark)
            X[chan][index] =  lightmean
            Y[chan][index] = lightvar
            
    myfile.close()


figlist, gslist = CreateFig(r'$\sigma^{2}_{image-dark}= (a+ b.x + c.x^2),\/with \/x = \mu_{image-dark}$',nchannel,sizeX=24.,sizeY=16.,)
fig = figlist[0]
gs = gslist[0]
ax = []
fig2list, gs2list = CreateFig(r'$\mu_{image-dark} =\/a+b.x(1+c.e^{d.x}),\/with \/x = Laser\/Power $',nchannel,sizeX=24.,sizeY=16.,)
fig2 = fig2list[0]
gs2 = gs2list[0]
ax2 = []
for chan in range(16):
    plt.figure(fig.number)
    ax.append(plt.subplot(gs[chan/4, chan%4]))
    plt.figure(fig2.number)
    ax2.append(plt.subplot(gs2[chan/4, chan%4]))
#def line(x): return slope()*x + offset()
def poly2(x): return a() +b()*x + c()*x*x
#def cutoff(x) : return (a() +b()*x + c()*x*x)*(1+np.exp(d()/(x-e())))
#def cutoff(x) : return (a() +b()*x + c()*x*x) + d()*x*x*x
def satur2(x): return a()+ b()*x*(1+c()*np.exp(d()*x))
#def satur(x): return c()*x*(1+a()*np.exp(b()*x))
for chan in range(16):
#    remove -1 the values which are left from the array creation (if some file were not used)
    plotx = np.delete(X[chan],np.where(X[chan]==-1))
    ploty = np.delete(Y[chan],np.where(X[chan]==-1))
#   Plot the data
    plt.figure(fig.number)
    plot = ax[chan].scatter(plotx,ploty,  linewidth = 0., c= laserpower, cmap=mpl.cm.rainbow,  marker = "*", s= 350)
    #  Fit a line per channel
#    slope = Parameter(1.)
#    offset = Parameter(1.)
#    fit(line,[slope,offset],ploty,plotx)
#    print slope.__call__(), offset.__call__()
#Fit a 2nd degree polynom
    a  = Parameter(1.)
    b  = Parameter(1.)
    c  = Parameter(1.)
#    d = Parameter(1.)
#    e = Parameter(1.)
    fit(poly2,[a,b,c],ploty,plotx) 
    print a.__call__(), b.__call__(), c.__call__()
#    ,d.__call__(),e.__call__()
#    #         Plot the fit
    continuousX = np.linspace(plotx.min(),plotx.max(),5000)
    ax[chan].plot(continuousX,[poly2(x) for x in continuousX],'--', marker = 'None')
#    fitlabel = "a = {:.3g}\nb = {:.3g}\nc = {:.3g}\nd = {:.3g}\ne = {:.3g}".format(a.__call__(),b.__call__(), c.__call__(),d.__call__(),e.__call__())
    fitlabel = "a = {:.3g}\nb = {:.3g}\nc = {:.3g}".format(a.__call__(),b.__call__(), c.__call__())
    ax[chan].text(0.07,0.65,fitlabel, transform=ax[chan].transAxes)
    ax[chan].set_title("Channel {}".format(chan))
    ax[chan].ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
    ax[chan].ticklabel_format(axis='y', style='sci', scilimits=(-2,4))
    del a, b, c
#    , d, e
#    second plot mean vs power
    plt.figure(fig2.number)
    plot2 = ax2[chan].scatter(laserpower,plotx,  linewidth = 0.,  marker = "*", s= 200)
    a = Parameter(1.)
    b = Parameter(1.)
    c = Parameter(1.)
    d = Parameter(1.)
    fit(satur2,[a,b,c, d],plotx,laserpower) 
    print a.__call__(), b.__call__(), c.__call__(), d.__call__()
#    #         Plot the fit
    continuousX = np.linspace(laserpower.min(),laserpower.max(),5000)
    ax2[chan].plot(continuousX,[satur2(x) for x in continuousX],'--', marker = 'None')
    fitlabel = "a = {:.3g}\nb = {:.3g}\nc = {:.3g}\nd = {:.3g}".format(a.__call__(),b.__call__(), c.__call__() ,d.__call__())
    ax2[chan].text(0.6,0.07,fitlabel, transform=ax2[chan].transAxes)
    ax2[chan].set_title("Channel {}".format(chan))
    ax2[chan].ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
    ax2[chan].ticklabel_format(axis='y', style='sci', scilimits=(-2,4))
    del a, b, c , d
plt.figure(fig.number)
gs.update(left=0.05,right= 0.85, top=0.90, bottom = 0.05, wspace=0.25,hspace=0.3)    
cbar_ax = fig.add_axes([0.9, 0.08, 0.02, 0.8])
cbar =fig.colorbar(plot, cax=cbar_ax)
cbar_ax.set_xlabel("\n Laser power \n in mW")
fig.savefig(dataDir+"./plots/light_varVSmean_{}.png".format(filelistname))
plt.figure(fig2.number)
fig2.savefig(dataDir+"./plots/light_meanVSlaserPower{}.png".format(filelistname))