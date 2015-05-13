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

    mapX,mapY, map,dark = BM.MakeRawImageMap(filename)
    # print mapX.shape, mapY.shape, map.shape
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
    im =plt.imshow(map, interpolation ='None', origin = 'upper', extent=[np.min(mapX),np.max(mapX),np.max(mapY),np.min(mapY)])
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
    signalMap = map - np.ones(map.shape)*avDark
    mymean = signalMap.mean()
    meanMap = mymean*np.ones(signalMap.shape)
    percent = (signalMap - meanMap )*100/meanMap
    label = 'signal above the average in %'

    plotname2 = plotDir+filename[:-5].replace(dataDir, "")+"_ImagePercent_"+source+".png"
    fig = plt.figure()
    ax=plt.subplot(111)
    im =plt.imshow(percent, interpolation ='None', origin = 'upper', extent=[np.min(mapX),np.max(mapX),np.max(mapY),np.min(mapY)])
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
    plotname3 = plotDir+filename[:-5].replace(dataDir, "")+"_ImagePercentFixedScale_"+source+".pdf"
    fig = plt.figure()
    ax=plt.subplot(111)
    im =plt.imshow(percent, interpolation ='None', origin = 'upper',extent=[np.min(mapX),np.max(mapX),np.max(mapY),np.min(mapY)] , vmin=mymin, vmax=mymax)
    ax.set_xlabel("X in mm")
    ax.set_ylabel("Y in mm")
    bar =fig.colorbar(im)
    bar.set_label(label)
    BM.PlotCCDLimit('black')
    fig.suptitle(title)
    plt.show()
    fig.savefig(plotname3)
    plt.close(fig)




    # # forth plot the same but zoomed
    # mymin = -1.
    # mymax = 1.
    # realxmin = 15
    # realxmax = 60
    # realymin = 5
    # realymax = 50
    # print map.shape[0], np.max(mapX) - np.min(mapX)
    # print (np.max(mapX) - np.min(mapX))/map.shape[0]
    # xmin = int(realxmin*map.shape[0]/(np.max(mapX) - np.min(mapX)))
    # xmax = int(realxmax*map.shape[0]/(np.max(mapX) - np.min(mapX)))
    # ymin = int(realymin*map.shape[1]/(np.max(mapY) - np.min(mapY)))
    # ymax = int(realymax*map.shape[1]/(np.max(mapY) - np.min(mapY)))
    # print xmin, xmax, ymin, ymax
    # plotname4 = plotDir+filename[:-5].replace(dataDir, "")+"_ImagePercentFixedScaleZoom_"+source+".png"
    # fig = plt.figure()
    # ax=plt.subplot(111)
    # im =plt.imshow(BM.crop(percent, xmin, xmax, ymin, ymax), interpolation ='None', origin = 'upper',aspect = None, extent=[realxmin, realxmax, realymax, realymin] , vmin=mymin, vmax=mymax)
    # ax.set_xlabel("X")
    # ax.set_ylabel("Y")
    # bar =fig.colorbar(im)
    # bar.set_label(label)
    # BM.PlotCCDLimit('black')
    # #plt.show()
    # # plt.xlim(xmin, xmax)
    # # plt.ylim(ymax, ymin)
    # fig.suptitle(title)
    # fig.savefig(plotname4)
    # plt.close(fig)

