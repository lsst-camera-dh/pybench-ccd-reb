__author__ = 'karkar'
import os, sys
import subprocess
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
import BeamMap.beamMaps as BM

if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/"

allfiles=[]
for (dirpath, dirnames, filenames) in os.walk(dataDir):
    for thisfile in filenames:
        if (thisfile[-5:] == '.data'):
            if "oldmaps" in dirpath: 
                continue
            allfiles.append(os.path.join(dirpath,thisfile))
if len(allfiles) == 0:
    print "Error no  .data files were found here :" , dataDir

print "will plot maps from files :", allfiles
allmethods = [BM.beamMap2d,BM.beamMapScatter2d, BM.beamMapScatter3d, BM.beamMapSurface3d]
print "using methods :", [method.__name__  for method in allmethods]

for plotMethod in allmethods:
    print "now using method: ", plotMethod.__name__
    for filename in allfiles:
        print 'now using file', filename
        b = np.genfromtxt(filename,  delimiter = ' ', skip_header = 4, usecols = (0,1,3))
        c = np.transpose(b)
        print c.shape
        X = c[0]
        Y = c[1]
        Z = c[2]
        plotname = filename[:-5]+"_"+plotMethod.__name__+".png"
        plotMethod(X,Y,Z, plotname)
#        subprocess.call(['python',plotMethod,filename])
