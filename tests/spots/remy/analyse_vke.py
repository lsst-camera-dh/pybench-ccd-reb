# Analyse les images prises par vke_beta et affiche le flux en fonction du deplacement
# Par remy Le Breton

import matplotlib.pyplot as plt
import pylab as py
import numpy as np
import scipy as sp
import sys
import os, os.path
import time

import math as m

import unicap
import Image
import pyfits as py
import glob as gl

fichiers = gl.glob("./vke_beta/*fits")
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

for j in data:
    cuts.append(j[y_min_cut:y_max_cut,x_min_cut:x_max_cut])



max_i = np.where(cuts[0]==np.max(cuts[0]))
max_i = [max_i[0][0], max_i[1][0] + 2]

flux = []

for c in cuts:
    flux.append(c[max_i[0]][max_i[1]])

plt.scatter(range(0, len(flux)), flux)
plt.xlabel("Displacement")
plt.ylabel("Flux in the studied pixel")
plt.title("VKE method")
plt.show()
