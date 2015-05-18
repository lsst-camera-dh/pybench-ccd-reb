__author__ = 'karkar'
import os, sys
import fileinput
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
# import FluxesPlots

def doPlot( plot, ch,laserpower, prefix):
    mytitle= plot[0]
    print mytitle
    imagename = mytitle.replace(" ","_")
    imagename = prefix+"_"+imagename+".png"
    print imagename
    X = plot[1]
    Y = plot[2]
    cut = plot[3]
    channellist = [1,2,3,4]
    for channel in channellist:
      cutcondition = (ch==channel) & cut
      plt.plot(X[cutcondition], Y[cutcondition], label="{}".format(channel), marker = "*", markeredgecolor= 'None', linewidth = 0)
    plt.grid(True)
    # plt.xlabel("X")
    # plt.ylabel("Y")
    plt.title(mytitle)
    plt.legend(title = "Laser channels ",numpoints = 1)
    plt.savefig(imagename)
    # fig.show()
    plt.close()





if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home-local/karkar/dataLSST/metrology/2015-04-28/"

# allfiles=[]
# maxdepth = 0
# for (dirpath, dirnames, filenames) in os.walk(dataDir):
#     depth = dirpath[len(dataDir) + len(os.path.sep):].count(os.path.sep)
#     if depth == maxdepth:
#         dirnames[:] = [] # Don't recurse any deeper
#     for thisfile in filenames:
#         if (thisfile[-5:] == '.data'):
#             allfiles.append(os.path.join(dirpath,thisfile))
# if len(allfiles) == 0:
#     print "Error no  .data files were found here :" , dataDir
#
# print "will plot from files :", allfiles

allfiles= glob.glob(dataDir+"/"+"DKD-PhD-Laser-fluxes*.data")
if len(allfiles) == 0 :
    print "no data file found in ", dataDir
    exit()
print "using data files: ", allfiles

#version with all files data concatenated
c = np.loadtxt(fileinput.input(allfiles,),comments='#', delimiter= ' ' , unpack=True, ndmin=0)

#version  with separated analysis for each file
# for filename in allfiles:
#     c = np.loadtxt(filename,comments='#', delimiter= ' ' , unpack=True, ndmin=0)

print c.shape
time = c[0]
ch = c[1]
lasercurrent= c[2]
laserpower=c[3]
DKDflux= c[4]
PhDFlux = c[5]


# list of plots with plot = (title, X, Y, cut)
# cut_time = (time > 1429939335.59)
# cut_oneloop = (time < 1430179848.34)
# cut_time = cut_oneloop
cut_time = True
allPlots = [('PhDFlux VS time', time, PhDFlux, cut_time),
            ('DKDflux VS time', time, DKDflux, cut_time),
            ('DKDflux VS laserpower', laserpower, DKDflux, cut_time),
            ('PhDFlux VS laserpower', laserpower, PhDFlux, cut_time),
            ('DKDflux VS lasercurrent', lasercurrent, DKDflux, cut_time),
            ('PhDFlux VS lasercurrent', lasercurrent, PhDFlux, cut_time),
            ('DKDflux VS PhDFlux', PhDFlux, DKDflux, cut_time),
            ('DKDflux VS PhDFlux low power', PhDFlux, DKDflux,(laserpower <2)& cut_time ),
            ('lasercurrent VS time', time, lasercurrent, cut_time),
            # ('laserpower VS time full range', time, laserpower, True),
            # ('lasercurrent VS time full range', time, lasercurrent, True),
            ('DKDflux Over PhDFlux VS time', time, DKDflux/PhDFlux, cut_time),
             ('DKDflux Over PhDFlux VS laserpower', laserpower, DKDflux/PhDFlux, cut_time),
             ]
            # cut_oneloop = ((time > 1429939335.59) & (time < 1429964839.88))

plotDir = dataDir+"/plots/"
if not os.path.isdir(plotDir):
            os.makedirs(plotDir)
print 'Data directory is :     %s' % dataDir
print 'Plot directory is :     %s' % plotDir
#version with all files data concatenated
prefix = dataDir+"/plots/"+"allData"
#version  with separated analysis for each file
# prefix = dataDir+"/plots/"+filename[:-5].replace(dataDir,"")
print prefix
# prefix = dataDir+"/plots/"+"oneLoop"
for plot in allPlots:
    print "now doing plot: ", plot[0]
    doPlot(plot,ch,laserpower, prefix )


