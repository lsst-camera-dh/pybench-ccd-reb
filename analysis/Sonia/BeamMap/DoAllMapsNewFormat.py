__author__ = 'karkar'
import os, sys
import numpy as np
import beamMaps as BM

if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home-local/karkar/dataLSST/metrology/testdata"

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
allmethods = [BM.beamMapScatter2dFixedScale, BM.beamMapScatter2d,BM.beamMap2d, BM.beamMapScatter3d, BM.beamMapSurface3d]
print "using methods :", [method.__name__  for method in allmethods]

for filename in allfiles:
    print 'now using file', filename
#         b = np.genfromtxt(filename,  delimiter = ' ', skip_header = 4, usecols = (0,1,3))
#         c = np.transpose(b)
    f = open(filename, "r")
    header = [f.readline() for x in range(3)]
    f.close()
    c = np.loadtxt(filename, comments='#', delimiter= ' ',  usecols=(1,2,4,5) , unpack=True, ndmin=0)
    print c.shape
    X = c[0]
    Y = c[1]
    Z = c[2]
    flagShutter = c[3]
    X = X[flagShutter==1]
    Y = Y[flagShutter==1]
    light = Z[flagShutter==1]
    dark = Z[flagShutter==0]
    # avLight = light.mean()
    avDark = dark.mean()
    signalMap = light - np.array([avDark]*light.shape[0])
    meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    percent = (signalMap - meanMap )*100/meanMap
    if flagShutter.shape[0] < 6:
        print "not enough valid points in this map, skipping"
	continue
    title = header
    label = 'signal above the average in percent'
    plotDir = dataDir+"/plots/"
    if not os.path.isdir(plotDir):
                os.makedirs(plotDir)
    print 'Data directory is :     %s' % dataDir
    print 'Plot directory is :     %s' % plotDir
    for plotMethod in allmethods:
        print "now using method: ", plotMethod.__name__
        plotname = plotDir+filename[:-5].replace(dataDir, "")+"_"+plotMethod.__name__+".png"
        if plotMethod == BM.beamMapScatter2dFixedScale:
            plotMethod(X,Y,percent, plotname, title, label, -2, 2)
        else:
            plotMethod(X,Y,percent, plotname, title, label)
