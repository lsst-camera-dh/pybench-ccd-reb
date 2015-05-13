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
allmethods = [ BM.beamMap2dFixedScale,BM.beamMap2d, BM.beamMapSurface3d]
# , BM.beamMapScatter2d, BM.beamMapScatter3d, BM.beamMapScatter2dFixedScale,
print "using methods :", [method.__name__  for method in allmethods]

for filename in allfiles:
    print 'now using file', filename
    #         b = np.genfromtxt(filename,  delimiter = ' ', skip_header = 4, usecols = (0,1,3))
    #         c = np.transpose(b)
    f = open(filename, "r")
    header = [f.readline() for x in range(3)]
    f.close()
    if "# Dark map (everything off)" in header[0]:
        print "Dark map will be treated separately, skipping"
        continue
    title = header
    # if "Laser channel" in header[0]:
    source = header[0].replace("# ", "").replace("= ", "").replace(" ", "_").replace("\n","")
    print source
    # else:
    #     ch = ""

    c = np.loadtxt(filename, comments='#', delimiter= ' ',  usecols=(1,2,4,5) , unpack=True, ndmin=0)
    print "data shape  is :", c.shape
    X = c[0]
    Y = c[1]
    Z = c[2]
    flagShutter = c[3]
    cutLight = flagShutter==1
    # npoints = flagShutter[cutLight].shape[0]

    X = X[cutLight]
    Y = Y[cutLight]
    light = Z[cutLight]
    dark = Z[flagShutter==0]

    uniqueX, indicesX = np.unique(X, return_index=True)
    uniqueY, indicesY = np.unique(Y, return_index=True)
    # print uniqueX, "\n",indicesX
    # print uniqueY,"\n", indicesY
    # uniqueX = [0.]
    # uniqueY = [0.]
    nmappoints = (uniqueX.shape[0])*(uniqueY.shape[0])
    if nmappoints < 6:
        print "only ", nmappoints, "points in this map, skipping"
        continue
    reducedX = np.zeros(nmappoints)
    reducedY = np.zeros(nmappoints)
    reducedmMap = np.zeros(nmappoints)
    i = 0
    for x in uniqueX:
        for y in uniqueY:
            allpointsXY = light[(X==x)&(Y==y)]
            # print "for (",x, y,") , Nmeasures = ", allpointsXY.shape[0]
            # print allpointsXY
            avMapPoint = allpointsXY.mean()
            # print "average for this point", avMapPoint
            reducedX[i] = x
            reducedY[i] = y
            reducedmMap[i] = avMapPoint
            i = i+1

    avDark = dark.mean()
    signalMap = reducedmMap - np.array([avDark]*reducedmMap.shape[0])
    meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    percent = (signalMap - meanMap )*100/meanMap
    label = 'signal above the average in percent'

    # if BM.diffMapScatter2d in allmethods:
    #     X1 =
    #     Y1 =
    #     Z1 =


    plotDir = dataDir+"/plots/"
    if not os.path.isdir(plotDir):
        os.makedirs(plotDir)
    print 'Data directory is :     %s' % dataDir
    print 'Plot directory is :     %s' % plotDir
    for plotMethod in allmethods:
        print "now using method: ", plotMethod.__name__
        plotname = plotDir+filename[:-5].replace(dataDir, "")+"_"+plotMethod.__name__+"_"+source+".png"
        if plotMethod == BM.beamMapScatter2dFixedScale or plotMethod == BM.beamMap2dFixedScale:
            plotMethod(reducedX,reducedY,percent, plotname, title, label, -2, 2)
        # elif  plotMethod == BM.diffMapScatter2d:
        #     plotMethod(X1,Y1,Z1, X2,Y2,Z2,plotname, title, label)
        else:
            plotMethod(reducedX,reducedY,percent, plotname, title, label)
    del c,X,Y,Z