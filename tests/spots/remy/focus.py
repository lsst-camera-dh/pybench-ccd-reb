#Pour le focus : prend des images le long de l'axe optique, et fit le spot en gaussien
#
#Raffinement du focus : 
#On teste sur les pixels adjacents [SUD,OUEST,EST,NORD] le ratio OUEST/EST et SUD/NORD.
#On veut que les deux soient proches de 1. Quand les deux sont proches de 1, le spot est centre.
#
#Par Remy Le Breton

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits as py
import scipy.optimize as opt
import pylab as pb
import glob as gl
import matplotlib.pyplot as plt

from fonctions import *
from math import *

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

#--------------------------------------------------------

mov = xyz.XYZ()

mov.x_port = '/dev/ttyUSB0'
mov.y_port = '/dev/ttyUSB1'
mov.z_port = '/dev/ttyUSB2'

mov.open()

cam = d.Camera()
cam.open()

#-----Revient a une position par defaut, apres avoir fait un home

mov.home()

default = np.loadtxt("default_pos.data", comments = '#')

xpos = default[0]
ypos = default[1]
zpos = default[2]

mov.move(x=xpos,y=ypos,z=zpos)

#------------------------------------------------

FOCUS(mov = mov, cam = cam, interval = 0.05, pas = 0.001)

fichiers = gl.glob("./focus/*.fits")
fichiers = sorted(fichiers)

images = []

for i in fichiers:
    images.append((py.open(i))[0])

donnees = []

for d in images:
    donnees.append(d.data)

params = []
fit = []

cuts = []

for k in donnees:
    cuts.append(CUT(k))

wx = np.array(params[:2][0])
wy = np.array(params[:3][0])

w_sum = abs(wx) + abs(wy)

NB_FOCUS = np.where(w_sum==np.min(w_sum))[0][0]

POS_FOCUS = images[NB_FOCUS].header['YPOS']

mov.move(y=POS_FOCUS)


#--Raffinement-du-focus-------------------------

expo = O.O2

data = cam.capture(exposure = expo)
cuts = CUT(data)

temp_max = np.where(cuts==np.max(cuts))
max_i = [temp_max[0][0], temp_max[1][0]]

pixels_flux = PF(cuts, max_i)
pixel_central_flux = PCF(cuts, max_i)

pas_raff = 0.0005
precision = 1.1 #Precision a laquelle on veut que les flux soient egaux

while((pixels_flux[1]/pixels_flux[2] > precision) or (pixels_flux[2]/pixels_flux[1] > precision)):
    if pixels_flux[1] > pixels_flux[2]:
        mov.move(dx=pas_raff)
    else:
        mov.move(dx=-pas_raff)

    temp_data = cam.capture(exposure = expo)
    temp_cuts = CUTS(temp_data)
    pixels_flux = PF(temp_cuts, max_i)
    pixel_central_flux = PCF(temp_cuts, max_i)


# while((pixels_flux[0]/pixels_flux[3] > precision) or (pixels_flux[3]/pixels_flux[0] > precision)):
#     if pixels_flux[0] > pixels_flux[3]:
#         mov.move(dz=pas_raff)
#     else:
#         mov.move(dz=-pas_raff)
    
#     temp_data = cam.capture(exposure = expo)
#     temp_cuts = CUTS(temp_data)
#     pixels_flux = PF(temp_cuts, max_i)
#     pixel_central_flux = PCF(temp_cuts, max_i)


VKE(mov=mov, cam=cam, pas = 0.0001)

#
#
# Faire scan vertical, estimer taille pixel, se placer au centre (en egalisant le flux sur deux pixel verticaux)
# se deplacer un peu, minimiser flux sur pixel superier, et ensuite cente
#
#

print("Changer les positions par defaut du focus (yes = 1/no = 0) ? : ")
suppr = input()

if suppr == 1:
    commande = "rm -f ./default_pos.data"
    os.system(commande)


    bar = open("default_pos.data", "w")
    bar.write('# XPOS, YPOS, ZPOS')
    bar.write('\n')
    bar.write(str(mov.x_axis.get_position()) + " " + str(mov.y_axis.get_position()) + " " + str(mov.z_axis.get_position()))
    bar.close()

