__author__ = 'karkar'
import os, sys
import subprocess
if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/"

allfiles=[]
for (dirpath, dirnames, filenames) in os.walk(dataDir):
    for thisfile in filenames:
        if (thisfile[-5:] == '.data'):
            allfiles.append(os.path.join(dirpath,thisfile))
if len(allfiles) == 0:
    print "Error no  .data files were found here :" , dataDir

print "will plot maps from files :", allfiles
allmethods = ['beamMap2d.py','beamMapScatter2d.py','beamMapScatter3d.py', 'beamMapsurface3d.py' ]
print "using methods :", allmethods

for plotMethod in allmethods:
    print "now using method: ", plotMethod
    for filename in allfiles:
        print 'now using file', filename
        subprocess.call(['python',plotMethod,filename])
