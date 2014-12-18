__author__ = 'karkar'
import os, sys
import numpy as np
import beamMaps as BM

if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home/karkar/SyncLPNHE/LSST/20140826"

allfiles=[]
maxdepth = 0
for (dirpath, dirnames, filenames) in os.walk(dataDir):
    depth = dirpath[len(dataDir) + len(os.path.sep):].count(os.path.sep)
    if depth == maxdepth:
        dirnames[:] = [] # Don't recurse any deeper
    for thisfile in filenames:
        if (thisfile[-5:] == '.data'):
            allfiles.append(os.path.join(dirpath,thisfile))
if len(allfiles) == 0:
    print "Error no  .data files were found here :" , dataDir

print "will plot maps from files :", allfiles
allmethods = [BM.beamMap2d,BM.beamMapScatter2d, BM.beamMapScatter3d, BM.beamMapSurface3d]
print "using methods :", [method.__name__  for method in allmethods]

for filename in allfiles:
    print 'now using file', filename
#         b = np.genfromtxt(filename,  delimiter = ' ', skip_header = 4, usecols = (0,1,3))
#         c = np.transpose(b)
    c = np.loadtxt(filename, comments='#', delimiter= ' ',  usecols=(0,1,2) , unpack=True, ndmin=0)
    print c.shape
    X = c[0]
    Y = c[1]
    Z = c[2]
    for plotMethod in allmethods:
        print "now using method: ", plotMethod.__name__
        plotname = filename[:-5]+"_"+plotMethod.__name__+".png"
        plotMethod(X,Y,Z, plotname)
