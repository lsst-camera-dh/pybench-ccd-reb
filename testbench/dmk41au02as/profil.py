import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits as py
import glob as gl

fichiers = gl.glob("./intensite/*fits")
fichiers = sorted(fichiers)

data = []

for i in fichiers:
    data.append((py.open(i))[0].data)

lines = np.shape(data[0])[0]
rows = np.shape(data[0])[1]

cuts = []

down = 14
up = 16
div = 30

x_min_cut = down*rows/div
y_min_cut = down*lines/div

x_max_cut = up*rows/div
y_max_cut = up*lines/div

indice = 0.1
compteur = 0

for j in data:
    cuts.append(j[y_min_cut:y_max_cut,x_min_cut:x_max_cut])
    py.writeto("./cuts/" + "cut_of_" + str(indice) + "s.fits", cuts[compteur], clobber = True)
    indice = indice + 0.1
    compteur = compteur + 1
