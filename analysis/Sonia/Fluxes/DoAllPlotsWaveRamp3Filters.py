__author__ = 'karkar'
import os, sys
import fileinput
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
# import FluxesPlots

def doPlot( plot, prefix, thetitle, filt):
    mytitle= plot[0]+" "+thetitle
    print mytitle
    imagename = mytitle.replace(" ","_").replace(":","")
    imagename = prefix+"_"+imagename+".pdf"
    print imagename
    X = plot[1]
    Y = plot[2]
    cut = plot[3]
    cutcondition = cut
    plt.plot(X[cutcondition], Y[cutcondition], label="filter {}".format(filt), marker = "*", markeredgecolor= 'None', linewidth = 0)
    plt.grid(True)
    plt.xlabel("$\lambda$ in nm")
    plt.ylabel("photodiode current (dark subtracted)")
    # plt.title(mytitle)
    plt.legend(numpoints = 1, loc =2 )
    # plt.savefig(imagename)
    # plt.show()
    # plt.close()





if len(sys.argv)>1:
    dataDir = sys.argv[1]
else:
    dataDir = "/home-local/karkar/dataLSST/metrology/2015-04-28/"

# allfiles=[]
# maxdepth = 0
# for (dirpath, dirnames, filenames) in os.walk(dataDir):
#     depth = dirpath[len(dataDir) + len(os.path.sep):].count(os.path.sep)
#     if depth == maxdepth:
#         dirnames[:] = [] # Don't recurse any deeper
#     for thisfile in filenames:
#         if (thisfile[-5:] == '.data'):
#             allfiles.append(os.path.join(dirpath,thisfile))
# if len(allfiles) == 0:
#     print "Error no  .data files were found here :" , dataDir
#
# print "will plot from files :", allfiles

# allfiles= glob.glob(dataDir+"/"+"DKD-PhD-QTH-triax-fluxes*.data")
allfiles=[dataDir+"/DKD-PhD-QTH-triax-fluxes-2015-05-15T00:35:30.190984.data", dataDir+"/DKD-PhD-QTH-triax-fluxes-2015-05-15T05:11:03.443241.data", dataDir+"/DKD-PhD-QTH-triax-fluxes-2015-05-15T09:47:18.740097.data"]
if len(allfiles) == 0 :
    print "no data file found in ", dataDir
    exit()
print "using data files: ", allfiles

#version with all files data concatenated
# c = np.loadtxt(fileinput.input(allfiles,),comments='#', delimiter= ' ' , unpack=True, ndmin=0)

#version  with separated analysis for each file
for filename in allfiles:
    print "now using data file: ", filename
    c = np.loadtxt(filename,comments='#', delimiter= ' ' , unpack=True, ndmin=0)

    print c.shape
    time = c[0]
    myfilter = c[1]
    grating = c[2]
    wavelength =c[3]
    lampCurrent = c[4]
    lampPower = c[5]
    DKDflux = c[6]
    PhDFlux = c[7]
    flagShutter = c[8]


    # list of plots with plot = (title, X, Y, cut)
    # cut_time = (time > 1429939335.59)
    # cut_oneloop = (time < 1430179848.34)
    # cut_time = cut_oneloop
    # cut = True
    cutlight = flagShutter == 1
    cutdark = flagShutter == 0
    darkDKD  = DKDflux[cutdark]
    darkPhD = PhDFlux[cutdark]
    DKDflux = DKDflux - darkDKD.mean()
    PhDFlux = PhDFlux - darkPhD.mean()

    darkDKDpercent = (darkDKD - darkDKD.mean())*100/ darkDKD.mean()
    darkPhDpercent = (darkPhD - darkPhD.mean())*100/ darkPhD.mean()

    allPlots = [
                # ('PhDFlux above dark VS time', time, PhDFlux, cutlight),
                # ('DKDflux above dark VS time', time, DKDflux, cutlight),
                ('PhDFlux above dark VS wavelength', wavelength, PhDFlux, cutlight),
                # ('DKDflux above dark  VS wavelength', wavelength, DKDflux, cutlight),
                # ('DKDflux above dark VS PhDFlux', PhDFlux, DKDflux, cutlight),
                # ('DKDflux Over PhDFlux VS time', time, DKDflux/PhDFlux, cutlight),
                # ('darkDKDPercent VS time', time[cutdark], darkDKDpercent, np.ones(darkDKDpercent.shape, dtype=bool) ),
                # ('darkPhDPercent VS time', time[cutdark], darkPhDpercent, np.ones(darkPhDpercent.shape, dtype=bool) ),
                 ]
                # cut_oneloop = ((time > 1429939335.59) & (time < 1429964839.88))

    plotDir = dataDir+"/plots/"
    if not os.path.isdir(plotDir):
                os.makedirs(plotDir)
    print 'Data directory is :     %s' % dataDir
    print 'Plot directory is :     %s' % plotDir
    #version with all files data concatenated
    # prefix = dataDir+"/plots/"+"allData"
    #version  with separated analysis for each file
    prefix = dataDir+"/plots/"+filename[:-5].replace(dataDir,"")
    print prefix
    # prefix = dataDir+"/plots/"+"oneLoop"
    # title = "filter: {}".format(int((myfilter[cutlight])[0]))+" grating: {}".format(int((grating[cutlight])[0]))
    title = ""
    for plot in allPlots:
        print "now doing plot: ", plot[0]
        doPlot(plot, prefix, title, int((myfilter[cutlight])[0]))
plt.show()
# plt.savefig(imagename)
plt.close()

