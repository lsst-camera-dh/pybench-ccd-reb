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

pas = 0.0005 #En mm
interval = 0.02
borne = int(interval/pas)
deplacement = 0

trou = "20micron"

for i in range(0,borne):
    cam.capture_and_save(exposure = 0.1, filename = "./vke_beta/aller_x_" + str(time.time()) + "_" + str(deplacement) + "mm_" + trou , filetype = "FITS")
    mov.move(dx=pas)
    deplacement = deplacement + pas

for i in range(0,borne):
    cam.capture_and_save(exposure = 0.1, filename = "./vke_beta/retour_x_" + str(time.time()) + "_" + str(deplacement) + "mm_" + trou , filetype = "FITS")
    mov.move(dx=-pas)
    deplacement = deplacement - pas
