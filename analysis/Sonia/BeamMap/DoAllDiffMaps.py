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

laser1List = []
laser2List = []
laser3List = []
laser4List = []
QTHList = []
for filename in allfiles:
    # print 'now using file', filename
    f = open(filename, "r")
    header = [f.readline() for x in range(3)]
    f.close()
    if "# Dark map (everything off)" in header[0]:
        print "Dark map will be treated separately, skipping"
        continue
    source = header[0].replace("# ", "").replace("= ", "").replace(" ", "_").replace("\n","")
    # print source
    if source == "Laser_channel_1":
        laser1List.append(filename)
    elif source == "Laser_channel_2":
        laser2List.append(filename)
    elif source == "Laser_channel_3":
        laser3List.append(filename)
    elif source == "Laser_channel_4":
        laser4List.append(filename)

# print "laser1", laser1List
# print "laser2",laser2List
# print "laser3",laser3List
# print "laser4", laser4List
# print QTHList

plotDir = dataDir+"/plots/"
if not os.path.isdir(plotDir):
    os.makedirs(plotDir)
print 'Data directory is :     %s' % dataDir
print 'Plot directory is :     %s' % plotDir

for sourceList in [laser1List,laser2List, laser3List, laser4List, QTHList]:
    print "using ", sourceList
    for ifile, filename1 in enumerate(sourceList):
        f = open(filename1, "r")
        sourceLine = f.readline()
        f.close()
        source = sourceLine.replace("# ", "").replace("= ", "").replace(" ", "_").replace("\n","")
        reducedsourceList = sourceList[ifile+1:]
        for filename2 in reducedsourceList:
            print "For",source , "comparing files ", filename1, " and ", filename2
            reducedX1,reducedY1,signalMap1, label1 = BM.MakeRawMap(filename1)
            reducedX2,reducedY2,signalMap2, label1 = BM.MakeRawMap(filename2)
            nmappoints = (reducedX1.shape[0])*(reducedY1.shape[0])
            if nmappoints < 6:
                print "only ", nmappoints, "points in this map, skipping"
                continue
            if (not (np.array_equal(reducedX1,reducedX2))) or (not (np.array_equal(reducedY1,reducedY2))):
                print "subtraction error: the two maps are different"
                continue

            title = "difference map"
            plotname = plotDir+filename1[:-5].replace(dataDir, "").replace("/","")+"Minus"+filename2[:-5].replace(dataDir, "").replace("/","")+"_"+source+".png"

            X = reducedX1
            Y = reducedY1
            Z = (signalMap1 - signalMap2)*100/signalMap1
            label = "difference in %"
            BM.beamMap2d(X,Y,Z,plotname,title,label)