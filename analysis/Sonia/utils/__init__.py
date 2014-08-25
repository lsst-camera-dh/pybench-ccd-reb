#import sys
#import time
import numpy as np
import pyfits
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
import math
import colorsys
from itertools import cycle

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.itervalues():
        sp.set_visible(False)

def get_color(color):
    for hue in range(color):
        hue = 1. * hue / color
        col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
        yield "#{0:02x}{1:02x}{2:02x}".format(*col)
        
def CreateFig(title,npad,sizeX=20.,sizeY=8., colfirst = True, DEBUG = True):
    nfig = int(math.ceil(npad/16.0))
    nlineperfig = min(int(math.ceil(npad/4.0)),4)
    ncolumnsperfig = min(npad,4)
#     print npad/maxcol
#     print math.ceil(npad/maxcol)
#     print int(math.ceil(npad/maxcol))
#     print min(int(math.ceil(npad/maxcol)),maxcol)
#     nlineperfig = min(int(math.ceil(npad/maxcol)),maxcol)
#     ncolumnsperfig = min(npad,maxcol)
#     print nlineperfig, ncolumnsperfig, maxcol
#     nfig = int(math.ceil(npad/(ncolumnsperfig*nlineperfig)))
    
    if colfirst:
        print "Plots will be arranged in:" , nfig, "figure(s),  with", nlineperfig, "line(s) and ", ncolumnsperfig, "column(s) of plot(s)"
    else :
        print "Plots will be arranged in:" , nfig, "figure(s),  with", nlineperfig, "line(s) and ", ncolumnsperfig, "line(s) of plot(s)"
    fig = []
    gs = []
    for i in range(nfig):
        if DEBUG:
            print "Creating figure" ,i
        if nfig>1 :
            fig.append(plt.figure(title+"_page{}".format(i), (sizeX,sizeY)))
            fig[i].suptitle(title+", page{}".format(i), fontsize=30, fontweight='bold', bbox={'boxstyle':'round4','facecolor':'red', 'alpha':0.2})
        else:
            fig.append(plt.figure(title, (sizeX,sizeY)))
            fig[i].suptitle(title,fontsize=30, fontweight='bold', bbox={'boxstyle':'round4','facecolor':'red', 'alpha':0.2})
        if colfirst:
            gs.append(gridspec.GridSpec(nlineperfig,ncolumnsperfig))
        else : 
            gs.append(gridspec.GridSpec(ncolumnsperfig,nlineperfig))
        gs[i].update(left=0.05,right= 0.95, top=0.90, bottom = 0.05, wspace=0.25,hspace=0.3)
    return fig,gs