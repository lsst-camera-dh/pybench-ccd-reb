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

import lsst.instruments.pollux.xyz as xyz
import lsst.instruments.dmk41au02as as d

opt_cut = "no"

#----Initialisation moteurs et camera----------------------------

mov = INIT_MOV()
mov.open()

cam = d.Camera()
cam.open()

#-----Revient a une position par defaut, apres avoir fait un home

position_depart = mov.get_position()

print position_depart
print "\n"
print "Rechercher les limites et faire un home ? (yes = 1 / no = 0) : "
make_home = input()
if make_home == 1:
    mov.home()

print "Aller aux coordonnees par default ? (yes = 1 / no = 0) : "
make_default = input()
if make_default == 1:
    MOVE_TO_DEFAULT(mov)

#-----Premiere etape du focus: minimisation de la taille du spot
foc = FOCUS(mov = mov, cam = cam, interval = 0.04, pas = 0.001, cut = opt_cut)
images, data, maxima, sums, ratios, ratio_pix_sup = INIT_IMAGES(foc)

print mov.get_position()

NB_FOCUS = np.where(ratios==np.max(ratios))[0][0]
POS_FOCUS = images[NB_FOCUS].header['YPOS']

mov.move(y=POS_FOCUS)

print mov.get_position()

cam.capture_and_save(exposure=test_expo, filename = "5micron", filetype = "FITS")
commande = "ds9 5micron.fits"
os.system(commande)


##--Raffinement-du-focus-------------------------
print mov.get_position()


FOCUS_EQ_EST_OUEST(mov, cam, cut = opt_cut)
cam.capture_and_save(exposure=test_expo, filename = "5micron", filetype = "FITS")
commande = "ds9 5micron.fits"
os.system(commande)
print mov.get_position()

FOCUS_EQ_VERTICAL(mov, cam, cut = opt_cut)
cam.capture_and_save(exposure=test_expo, filename = "5micron", filetype = "FITS")
commande = "ds9 5micron.fits"
os.system(commande)
print mov.get_position()

mov.move(dz=-0.001) #Verifier le sens

#On minimise le flux dans le pixel au dessus de celui max, et on retourne a la position
print mov.get_position()

foc_raff = FOCUS(mov = mov, cam = cam, interval = 0.001, pas = 0.0001, cut = opt_cut)
images_raff, data_raff, maxima_raff, sums_raff, ratios_raff, ratios_pix_sup_raff = INIT_IMAGES(foc_raff)

print mov.get_position()

NB_FOCUS_RAFF = np.where(ratios_pix_sup_raff==np.min(ratios_pix_sup_raff))[0][0]
POS_FOCUS_RAFF = images_raff[NB_FOCUS_RAFF].header['YPOS']

mov.move(y=POS_FOCUS_RAFF)

print mov.get_position()

CHANGE_DEFAULT_POS(mov)


