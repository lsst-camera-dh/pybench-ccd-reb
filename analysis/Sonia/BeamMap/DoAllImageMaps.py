__author__ = 'karkar'
import os, sys
import numpy as np
import beamMaps as BM
import matplotlib.pyplot as plt

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
    f = open(filename, "r")
    firstLine = f.readline()
    f.close()
    source = firstLine.replace("# ", "").replace("= ", "").replace(" ", "_").replace("\n","")
    if "# Dark map (everything off)" in firstLine:
        print "Dark map will be treated separately, skipping"
        continue
    title = source
    print source

    uniqueX,uniqueY, map,dark = BM.MakeRawImageMap(filename)
    label = "PhD current"
    nmappoints = map.shape[0]*map.shape[1]
    if nmappoints < 6:
        print "only ", nmappoints, "points in this map, skipping"
        continue

    # avDark = dark.mean()
    # signalMap = reducedmMap - np.array([avDark]*reducedmMap.shape[0])
    # meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    # percent = (signalMap - meanMap )*100/meanMap
    # label = 'signal above the average in percent'

    plotDir = dataDir+"/plots/"
    if not os.path.isdir(plotDir):
        os.makedirs(plotDir)
    print 'Data directory is :     %s' % dataDir
    print 'Plot directory is :     %s' % plotDir

#   first plot the raw image
    plotname = plotDir+filename[:-5].replace(dataDir, "")+"_Image_"+source+".png"
    fig = plt.figure()
    ax=plt.subplot(111)
    im =plt.imshow(map, interpolation ='None', origin = 'lower', extent=[min(uniqueX),max(uniqueX),min(uniqueY),max(uniqueY)])
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    BM.PlotCCDLimit('black')
    #plt.show()
    fig.suptitle(title)
    fig.savefig(plotname)
    plt.close(fig)

#   second plot is relative to the average value of the map and in percent
    avDark = dark.mean()
    signalMap = map - np.array([avDark]*map.shape[0])
    meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    percent = (signalMap - meanMap )*100/meanMap
    label = 'signal above the average in percent'

    plotname2 = plotDir+filename[:-5].replace(dataDir, "")+"_ImagePercent_"+source+".png"
    fig = plt.figure()
    ax=plt.subplot(111)
    im =plt.imshow(percent, interpolation ='None', origin = 'lower', extent=[min(uniqueX),max(uniqueX),min(uniqueY),max(uniqueY)])
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    BM.PlotCCDLimit('black')
    #plt.show()
    fig.suptitle(title)
    fig.savefig(plotname2)
    plt.close(fig)


    # third plot the same but with fixed percent scale
    mymin = -1.
    mymax = 1.
    plotname3 = plotDir+filename[:-5].replace(dataDir, "")+"_ImagePercentFixedScale_"+source+".png"
    fig = plt.figure()
    ax=plt.subplot(111)
    im =plt.imshow(percent, interpolation ='None', origin = 'lower', extent=[min(uniqueX),max(uniqueX),min(uniqueY),max(uniqueY)], vmin=mymin, vmax=mymax)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    BM.PlotCCDLimit('black')
    #plt.show()
    fig.suptitle(title)
    fig.savefig(plotname3)
    plt.close(fig)