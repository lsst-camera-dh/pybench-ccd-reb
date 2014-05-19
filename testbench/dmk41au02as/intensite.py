#Pour le focus
#Par Remy Le Breton

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits

import lsst.testbench.pollux.xyz as xyz
import dmk41au02as as d

mov = xyz.XYZ()

mov.x_port = '/dev/ttyUSB0'
mov.y_port = '/dev/ttyUSB1'
mov.z_port = '/dev/ttyUSB2'

mov.open()

cam = d.Camera()
cam.open()

trou = "pose"

for i in range(0,2*borne):
    mov.move(dy=pas)
    cam.capture_and_save(exposure = 1, filename = str(i) + "_" + trou , filetype = "FITS")
