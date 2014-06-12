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

mov = INIT_MOV()
mov.open()

cam = d.Camera()
cam.open()

maxima = []

for i in range(0,2):
    mov.home()
    MOVE_TO_DEFAULT(mov)

    img = cam.capture(exposure = expo)
    mov.move(dx=pas)
    img = np.array(img)

    name = "test_home.data"
    temp_max = np.where(img==np.max(img))
    max_i = [temp_max[0][0], temp_max[1][0]]
    r = open(name, mode = "w")

    r.write(max_i[0])
    r.write(" ")
    r.write(max_i[1])
    r.write("\n")

    r.close()

# prendre une image
