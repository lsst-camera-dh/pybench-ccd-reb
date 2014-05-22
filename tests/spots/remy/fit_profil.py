from pylab import *
from numpy import *
from scipy import optimize
import sys
import os, os.path
import time

import unicap
import Image
import pyfits as py
import glob as gl

def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*exp(-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    data = data + 0.000000000000000001
    total = data.sum()
    X, Y = indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    col_sum = col.sum()

    if col_sum == 0:
        col_sum = 0.000000001

    width_x = sqrt(abs((arange(col.size)-y)**2*col).sum()/col_sum)
    row = data[int(x), :]
    row_sum = row.sum()

    if row_sum == 0:
        row_sum = 0.000000001

    width_y = sqrt(abs((arange(row.size)-x)**2*row).sum()/row_sum)
    height = data.max()
    return height, x, y, width_x, width_y

def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: ravel(gaussian(*p)(*indices(data.shape)) - data)
    p, success = optimize.leastsq(errorfunction, params)
    return p

fichiers = gl.glob("./focus/*fits")
fichiers = sorted(fichiers)

data = []

for i in fichiers:
    data.append((py.open(i))[0].data)

lines = np.shape(data[0])[0]
rows = np.shape(data[0])[1]

cuts = []

down = 15
up = 17
div = 30

x_min_cut = down*rows/div
y_min_cut = down*lines/div

x_max_cut = up*rows/div
y_max_cut = up*lines/div

indice = 0.1
compteur = 0

#for j in data:
 #   cuts.append(j[y_min_cut:y_max_cut,x_min_cut:x_max_cut])
  #  indice = indice + 0.1
   # compteur = compteur + 1

for j in data:
    cuts.append(j[y_min_cut:y_max_cut,x_min_cut:x_max_cut])
    #py.writeto("./cuts/" + "cut_of_" + str(indice) + "s.fits", cuts[compteur], clobber = True)
    #indice = indice + 0.1
    #compteur = compteur + 1


params = []
fit = []

for i in cuts:
    matshow(i, cmap=cm.gist_earth_r)
    plt.xlim(30,50)
    plt.ylim(30,40)

    param_i = fitgaussian(i)
    params.append(param_i)

    fit_i = gaussian(*param_i)
    fit.append(fit_i)

    contour(fit_i(*indices(i.shape)), cmap=cm.copper)
    ax = gca()
    (height, x, y, width_x, width_y) = param_i

    text(0.95, 0.05, """
       x : %.1f
       y : %.1f
       width_x : %.1f
       width_y : %.1f""" %(x, y, width_x, width_y),
         fontsize=16, horizontalalignment='right',
         verticalalignment='bottom', transform=ax.transAxes)

    show()
