#Author : Remy Le Breton

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D

import numpy as np
import os, sys
import glob as gl
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
    #bar.set_label("Standard deviation")
    #plt.show()
    fig.savefig(plotname)

def plotstab(A, B, n):
    m, b = np.polyfit(A, B[n], 1)

    plt.plot(A, B[n], '.')
    plt.plot(A, m*A + b, '-')
    plt.title("STD:" + str(np.std(B[n])) + " & " + "coef:" + str(m))
    plt.show()
    print m


f = gl.glob("*.data")
f.sort()

X = []
Y = []
Z = []

for filename in f:
    c = np.loadtxt(filename, comments='#', delimiter= ' ',  usecols=(0,1,2) , unpack=True, ndmin=0)
    X = c[0]
    Y = c[1]
    Z.append(c[2])

Si = []
S = []
M = []

for i in xrange(len(X)):
    s = []
    m = []
    for z in Z:
        s.append(z[i])
    Si.append(s)
    S.append(np.std(s))
    M.append(np.mean(s))

S = np.array(S)
M = np.array(M)

R = S/M

beamMap2d(X,Y,S, "std_122_maps")
beamMap2d(X,Y,R, "std-mean-ratio")

a =  xrange(len(Z))

plt.clf()
plt.axhline(y=np.mean(M[1]))
plt.scatter(a,Si[1])
plt.show()
plt.clf()

#for n in xrange(len(Si)):
#    plotstab(a,Si,n)



