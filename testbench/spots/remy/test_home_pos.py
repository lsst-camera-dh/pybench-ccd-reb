import sys
import os, os.path
import time

import numpy as np
import pyfits as py

from math import *

import lsst.instruments.pollux.xyz as xyz

mov = xyz.XYZ()
mov.open()

nb_boucles = 20

name = "test_home_pos/" + str(time.time()) + ".data"
r = open(name, mode = "w")

for i in range(0,nb_boucles):
    mov.home()

    x = mov.x_axis.get_limits()
    y = mov.y_axis.get_limits()
    z = mov.z_axis.get_limits()

    r.write(str(x['down']))
    r.write(" ")
    r.write(str(x['up']))
    r.write(" ")
    r.write(str(y['down']))
    r.write(" ")
    r.write(str(y['up']))
    r.write(" ")
    r.write(str(z['down']))
    r.write(" ")
    r.write(str(z['up']))
    r.write(" ")
    r.write("\n")

    print i

r.close()
