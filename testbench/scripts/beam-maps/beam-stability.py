#Author : Remy Le Breton

import os, sys
import numpy as np

if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/LSST/lsst/py/testbench/scripts/beam-maps/2014102324"

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
