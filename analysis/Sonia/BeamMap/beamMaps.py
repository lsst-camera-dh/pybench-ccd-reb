import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np



def MakeRawMap(filename,xmin=-1, xmax=-1, ymin=-1, ymax=-1):
    c = np.loadtxt(filename, comments='#', delimiter= ' ',  usecols=(1,2,4,5) , unpack=True, ndmin=0)
    print "raw data shape  is :", c.shape
    if xmin == -1:
        xmin =c[0].min()
    if xmax == -1:
        xmax =c[0].max()
    if ymin == -1:
        ymin =c[1].min()
    if ymax == -1:
        ymax =c[1].max()
    # cutX  = (c[0]>xmin)&(c[0]<xmax)
    # cutY  = (c[1]>ymin)&(c[1]<ymax)
    # zoom = cutX&cutY
    # c = c[zoom]
    # print "cropped data shape  is :", c.shape
    X = c[0]
    Y = c[1]
    Z = c[2]
    flagShutter = c[3]


    cutLight = flagShutter==1
    X = X[cutLight]
    Y = Y[cutLight]
    light = Z[cutLight]
    dark = Z[flagShutter==0]
    print "original data shape  is :", X.shape, Y.shape, light.shape, dark.shape

    cutX  = (X>=xmin)&(X<=xmax)
    cutY  = (Y>=ymin)&(Y<=ymax)
    zoom = cutX&cutY
    # c = c[zoom]

    X = X[zoom]
    Y = Y[zoom]
    light = light[zoom]

    print "cropped data shape  is :", X.shape, Y.shape, light.shape


    uniqueX, indicesX = np.unique(X, return_index=True)
    uniqueY, indicesY = np.unique(Y, return_index=True)
    nmappoints = (uniqueX.shape[0])*(uniqueY.shape[0])
    reducedX = np.zeros(nmappoints)
    reducedY = np.zeros(nmappoints)
    reducedmMap = np.zeros(nmappoints)
    i = 0
    for x in uniqueX:
        for y in uniqueY:
            allpointsXY = light[(X==x)&(Y==y)]
            avMapPoint = allpointsXY.mean()
            reducedX[i] = x
            reducedY[i] = y
            reducedmMap[i] = avMapPoint
            i = i+1
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

    X = X[cutLight]
    Y = Y[cutLight]
    light = Z[cutLight]
    dark = Z[flagShutter==0]

    uniqueX, indicesX = np.unique(X, return_index=True)
    uniqueY, indicesY = np.unique(Y, return_index=True)
    nmappoints = (uniqueX.shape[0])*(uniqueY.shape[0])
    allpointsXY = {}
    reducedMap= {}
    i = 0
    for x in uniqueX:
        for y in uniqueY:
            allpointsXY[(x,y)]= light[(X==x)&(Y==y)]
            reducedMap[(x,y)] = allpointsXY[(x,y)].mean()
    map = np.array([np.array([reducedMap[(x,y)] for x in uniqueX]) for y in uniqueY])
    # mapX = X.reshape((uniqueX.shape[0],uniqueY.shape[0]))
    # mapY = Y.reshape((uniqueX.shape[0],uniqueY.shape[0]))
    return uniqueX,uniqueY,map,dark

def PlotCCDLimit(mycolor='black'):
    plt.plot((17, 57), (7, 7), linewidth = 3, color = mycolor)
    plt.plot((17, 57), (47, 47), linewidth = 3, color = mycolor)
    plt.plot((17, 17), (7, 47), linewidth = 3, color = mycolor)
    plt.plot((57, 57), (7, 47), linewidth = 3, color = mycolor)

def beamMap2d(X,Y,Z,plotname,mytitle,label):
    xi = np.linspace(min(X), max(X), num=np.unique(X).shape[0])
    yi = np.linspace(min(Y), max(Y), num=np.unique(Y).shape[0])
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax=plt.subplot(111)
    im =ax.pcolor(X,Y,Z)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    PlotCCDLimit('black')
    #plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)


def beamMap2dFixedScale(X,Y,Z,plotname,mytitle,label, mymin, mymax, ):
    xi = np.linspace(min(X), max(X), num=np.unique(X).shape[0])
    yi = np.linspace(min(Y), max(Y), num=np.unique(Y).shape[0])
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax=plt.subplot(111)
    im =ax.pcolor(X,Y,Z, vmin=mymin, vmax=mymax)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar =fig.colorbar(im)
    bar.set_label(label)
    PlotCCDLimit('black')
    #plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)



def beamMapScatter2d(X,Y,Z,plotname,mytitle, label):
    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.scatter(X,Y, c= Z, cmap=mpl.cm.rainbow, s =100)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar = fig.colorbar(im)
    bar.set_label(label)
    PlotCCDLimit('black')
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)
def beamMapScatter2dFixedScale(X,Y,Z,plotname,mytitle,label, mymin, mymax):
    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.scatter(X,Y, c= Z, vmin=mymin, vmax=mymax, cmap=mpl.cm.rainbow, s =100)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar = fig.colorbar(im)
    bar.set_label(label)
    PlotCCDLimit('black')
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)
def beamMapScatter3d(X,Y,Z,plotname,mytitle, label):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    im = ax.scatter(X,Y,Z,c= Z, cmap=mpl.cm.rainbow, s = 10 )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel(label)
    bar = fig.colorbar(im)
    bar.set_label(label)
    PlotCCDLimit('black')
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)
def beamMapSurface3d(X,Y,Z,plotname,mytitle, label):
    xi = np.linspace(min(X), max(X), num=np.unique(X).shape[0])
    yi = np.linspace(min(Y), max(Y), num=np.unique(Y).shape[0])
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=mpl.cm.coolwarm,linewidth=0, antialiased=False)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel(label)
    PlotCCDLimit('black')
    fig.colorbar(surf, shrink=0.5, aspect=5)
    # plt.show()
    fig.suptitle(mytitle)
    fig.savefig(plotname)
    plt.close(fig)
