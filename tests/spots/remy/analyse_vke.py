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
position = []

for i in fichiers:
    temp = py.open(i)
    data.append(temp[0].data)
    position.append(temp[0].header['ZPOS'])

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
max_i = [max_i[0][0] + 1, max_i[1][0]] #Pixel voision du pixel central

max_i2 = np.where(cuts[0]==np.max(cuts[0]))
max_i2 = [max_i2[0][0] + 2, max_i2[1][0]]

flux = []
flux2 = []

for c in cuts:
    flux.append(c[max_i[0]][max_i[1]])
    flux2.append(c[max_i2[0]][max_i2[1]])

pas_deb = fichiers[1].find("0.")
pas_fin = fichiers[1].find("mm")
pas = fichiers[1][pas_deb:pas_fin + 2]
step = float(fichiers[1][pas_deb:pas_fin])

#xs = np.arange(0.,len(flux))
#xs *= step*1000 #En micron

#xs = np.arange(0.,len(flux)/2)
#xs *= step*1000
#xs = list(xs) + list(xs[::-1] + 0.2)


plt.scatter(position, flux, marker = '+', color = 'b')
plt.scatter(position, flux2, marker = '+', color = 'r')
plt.xlabel("Position")
plt.ylabel("Flux")
plt.title("Step of " + pas)
plt.show()
