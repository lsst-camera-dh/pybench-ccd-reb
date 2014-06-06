#Procedure de focalisation en plusieurs etapes
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

#----Initialisation moteurs et camera----------------------------

mov = INIT_MOV()
mov.open()

cam = d.Camera()
cam.open()

#-----Revient a une position par defaut, apres avoir fait un home

mov.home()
MOVE_TO_DEFAULT()

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



wx = np.array(params[:2][0])
wy = np.array(params[:3][0])

w_sum = abs(wx) + abs(wy)

NB_FOCUS = np.where(w_sum==np.min(w_sum))[0][0]

POS_FOCUS = images[NB_FOCUS].header['YPOS']

mov.move(y=POS_FOCUS)


#--Raffinement-du-focus-------------------------

VKE(mov=mov, cam=cam, pas = 0.0001)

FOCUS_EQ_EST_OUEST(mov, cam)

CHANGE_DEFAULT_POS(mov)

#
#
# Faire scan vertical, estimer taille pixel, se placer au centre (en egalisant le flux sur deux pixel verticaux)
# se deplacer un peu, minimiser flux sur pixel superier, et ensuite cente
#
#


