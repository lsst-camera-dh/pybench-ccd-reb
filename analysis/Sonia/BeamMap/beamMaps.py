import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def beamMap2d(X,Y,Z,plotname):
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
    bar.set_label("photodiode current")
    #plt.show()
    fig.savefig(plotname)
    
def beamMapScatter2d(X,Y,Z,plotname):
    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.scatter(X,Y, c= Z, cmap=mpl.cm.rainbow, s =400)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    bar = fig.colorbar(im)
    bar.set_label("photodiode current")
    # plt.show()
    fig.savefig(plotname)
    
def beamMapScatter3d(X,Y,Z,plotname):   
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    im = ax.scatter(X,Y,Z,c= Z, cmap=mpl.cm.rainbow, s = 150 )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Photodiode current")
    bar = fig.colorbar(im)
    bar.set_label("photodiode current")
    # plt.show()
    fig.savefig(plotname)
def beamMapSurface3d(X,Y,Z,plotname):
    xi = np.linspace(min(X), max(X))
    yi = np.linspace(min(Y), max(Y))
    Z = griddata(X,Y,Z, xi, yi)
    X, Y = np.meshgrid(xi, yi)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=mpl.cm.coolwarm,linewidth=0, antialiased=False)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Photodiode current")
    fig.colorbar(surf, shrink=0.5, aspect=5)
    # plt.show()
    fig.savefig(plotname)