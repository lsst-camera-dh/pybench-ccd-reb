import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def MakeRawMap(filename):
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

    # avDark = dark.mean()
    # signalMap = reducedmMap - np.array([avDark]*reducedmMap.shape[0])
    # meanMap = np.array([signalMap.mean()]*signalMap.shape[0])
    # percent = (signalMap - meanMap )*100/meanMap
    label = 'PhD current'

    return reducedX,reducedY,reducedmMap,dark, label

def MakeRawImageMap(filename):
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
    # reducedX = np.zeros(nmappoints)
    # reducedY = np.zeros(nmappoints)
    allpointsXY = {}
    reducedMap= {}
    i = 0
    for x in uniqueX:
        for y in uniqueY:
            allpointsXY[(x,y)]= light[(X==x)&(Y==y)]
            reducedMap[(x,y)] = allpointsXY[(x,y)].mean()
    map = np.array([np.array([reducedMap[(x,y)] for x in uniqueX]) for y in uniqueY])
    # return uniqueX,uniqueY,allpointsXY, reducedMap
    return uniqueX,uniqueY,map


def beamMap2d(X,Y,Z,plotname,mytitle,label):
    xi = np.linspace(min(X), max(X))
    yi = np.linspace(min(Y), max(Y))
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax=plt.subplot(111)
    im =ax.pcolor(X,Y,Z)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    #plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)

def beamMap2dFixedScale(X,Y,Z,plotname,mytitle,label, mymin, mymax):
    xi = np.linspace(min(X), max(X))
    yi = np.linspace(min(Y), max(Y))
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax=plt.subplot(111)
    im =ax.pcolor(X,Y,Z, vmin=mymin, vmax=mymax)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    #plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)


def beamMapScatter2d(X,Y,Z,plotname,mytitle, label):
    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.scatter(X,Y, c= Z, cmap=mpl.cm.rainbow, s =100)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar = fig.colorbar(im)
    bar.set_label(label)
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)

def beamMapScatter2dFixedScale(X,Y,Z,plotname,mytitle,label, mymin, mymax):
    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.scatter(X,Y, c= Z, vmin=mymin, vmax=mymax, cmap=mpl.cm.rainbow, s =100)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar = fig.colorbar(im)
    # bar.set_clim(min, max)
    bar.set_label(label)
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)

def beamMapScatter3d(X,Y,Z,plotname,mytitle, label):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    im = ax.scatter(X,Y,Z,c= Z, cmap=mpl.cm.rainbow, s = 10 )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel(label)
    bar = fig.colorbar(im)
    bar.set_label(label)
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)

def beamMapSurface3d(X,Y,Z,plotname,mytitle, label):
    xi = np.linspace(min(X), max(X))
    yi = np.linspace(min(Y), max(Y))
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=mpl.cm.coolwarm,linewidth=0, antialiased=False)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel(label)
    fig.colorbar(surf, shrink=0.5, aspect=5)
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)

