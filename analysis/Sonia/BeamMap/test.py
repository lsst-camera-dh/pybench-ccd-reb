__author__ = 'karkar'
import os, sys
import numpy as np
import BeamMap.beamMaps as BM

if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/"

allfiles=[]
maxdepth = 1
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
print len(allfiles)