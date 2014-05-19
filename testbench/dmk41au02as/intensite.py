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

trou = "20micron"
pose = "pose_de_"

pas = 0.1
maxtemps = 1
borne = int(maxtemps/0.1)
temps = pas

for i in range(0,borne):
    
    cam.capture_and_save(exposure = temps, filename = "intensite/" + pose + str(temps)+ "s" + "_" + trou , filetype = "FITS")
    #time.sleep(temps)
    temps = temps + pas
