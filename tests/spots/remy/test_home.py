import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits as py

from fonctions import *
from math import *

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

mov = INIT_MOV()
mov.open()

cam = d.Camera()
cam.open()

maxima = []

name = "test_home.data"
r = open(name, mode = "w")

for i in range(0,2):
    mov.home()
    MOVE_TO_DEFAULT(mov)

    img = cam.capture(exposure = expo)
    mov.move(dx=pas)
    img = np.array(img)

    temp_max = np.where(img==np.max(img))
    max_i = [temp_max[0][0], temp_max[1][0]]

    r.write(str(max_i[0]))
    r.write(" ")
    r.write(str(max_i[1]))
    r.write(" ")
    r.write(str(img[max_i[0],max_i[1]]))
    r.write("\n")

r.close()
