#Pour le focus : prend des images le long de l'axe optique, et fit le spot en gaussien
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

pas = 0.001 #En mm
interval = 0.005
borne = int(interval/pas)

mov.move(dy=-interval)

trou = "20micron"

for i in range(0,2*borne):
    mov.move(dy=pas)
    cam.capture_and_save(exposure = 0.1, filename = "./focus/" + str(time.time()) + "_" + trou , filetype = "FITS")
