#Methode VKE : deplace le spot lumineux le long d'une rangee ou colonne de pixel, sauvegarde des images fits
#Par Remy Le Breton

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

mov = xyz.XYZ()

mov.x_port = '/dev/ttyUSB0'
mov.y_port = '/dev/ttyUSB1'
mov.z_port = '/dev/ttyUSB2'

mov.open()

cam = d.Camera()
cam.open()

pas = 0.0002 #En mm
interval = 0.02
borne = int(interval/pas)
deplacement = 0

trou = "20micron"

#
# Supprimer le contenu de ./vke_beta
#

for i in range(0,borne):

    XPOS = mov.x_axis.get_position()
    
    name = "./vke_beta/aller_x_" + str(time.time()) + "_" + str(deplacement) + "mm_" + trou 
    cam.capture_and_save(exposure = 0.05, filename = name, filetype = "FITS")
    mov.move(dx=pas)
    deplacement = deplacement + pas

    update = py.open(name)
    update[0].header.update('xpos', XPOS)
    update.close()

for i in range(0,borne):

    XPOS = mov.x_axis.get_position()
    
    mov.move(dx=-pas)
    deplacement = deplacement - pas
    name = "./vke_beta/aller_x_" + str(time.time()) + "_" + str(deplacement) + "mm_" + trou
    cam.capture_and_save(exposure = 0.05, filename = name , filetype = "FITS")
    
    update = py.open(name)
    update[0].header.update('xpos', XPOS)
    update.close()
