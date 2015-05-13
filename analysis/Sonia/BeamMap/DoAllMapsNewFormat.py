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
allmethods = [ BM.beamMap2dFixedScale,BM.beamMap2d]
# BM.beamMapSurface3d]
# , BM.beamMapScatter2d, BM.beamMapScatter3d, BM.beamMapScatter2dFixedScale,
print "using methods :", [method.__name__  for method in allmethods]

for filename in allfiles:
    print 'now using file', filename
    f = open(filename, "r")
    firstLine = f.readline()
    f.close()
    source = firstLine.replace("# ", "").replace("= ", "").replace(" ", "_").replace("\n","")
    if "# Dark map (everything off)" in firstLine:
        print "Dark map will be treated separately, skipping"
        continue
    title = source
    print source

    reducedX,reducedY,reducedmMap,dark, label = BM.MakeRawMap(filename)
    nmappoints = (reducedX.shape[0])*(reducedY.shape[0])
    if nmappoints < 6:
        print "only ", nmappoints, "points in this map, skipping"
        continue
    avDark = dark.mean()
    signalMap = reducedmMap - np.array([avDark]*reducedmMap.shape[0])
    meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    percent = (signalMap - meanMap )*100/meanMap
    label = 'signal above the average in percent'





    plotDir = dataDir+"/plots/"
    if not os.path.isdir(plotDir):
        os.makedirs(plotDir)
    print 'Data directory is :     %s' % dataDir
    print 'Plot directory is :     %s' % plotDir

    # min max for colorscale
    mymin = -1
    mymax = 1
    for plotMethod in allmethods:
        print "now using method: ", plotMethod.__name__
        plotname = plotDir+filename[:-5].replace(dataDir, "")+"_"+plotMethod.__name__+"_"+source+".png"
        if plotMethod == BM.beamMapScatter2dFixedScale or plotMethod == BM.beamMap2dFixedScale:
            plotMethod(reducedX,reducedY,percent, plotname, title, label,mymin, mymax)
        else:
            plotMethod(reducedX,reducedY,percent, plotname, title, label)

    # min max for colorscale
    mymin = -1.
    mymax = 1.
    # min max for zoom
    xmin = 15
    xmax = 60
    ymin = 5
    ymax = 50
    reducedX2,reducedY2,reducedmMap2,dark2, label2= BM.MakeRawMap(filename,xmin, xmax, ymin, ymax )
    nmappoints2 = (reducedX2.shape[0])*(reducedY2.shape[0])
    if nmappoints2 < 6:
        print "only ", nmappoints, "points in this map, skipping"
        continue
    avDark2 = dark2.mean()
    signalMap2 = reducedmMap2 - np.array([avDark2]*reducedmMap2.shape[0])
    meanMap2 = np.array([signalMap2.mean()]*signalMap2.shape[0])
    percent2 = (signalMap2 - meanMap2 )*100/meanMap2
    label2 = 'signal above the average in percent'

    for plotMethod in allmethods:
        print "now using method: ", plotMethod.__name__
        plotname2 = plotDir+filename[:-5].replace(dataDir, "")+"_"+plotMethod.__name__+"Zoom_"+source+".png"
        if plotMethod == BM.beamMapScatter2dFixedScale or plotMethod == BM.beamMap2dFixedScale:
            plotMethod(reducedX2,reducedY2,percent2, plotname2, title, label2,mymin, mymax)
        else:
            plotMethod(reducedX2,reducedY2,percent2, plotname2, title, label2)