import sys
import os, os.path
import time
import unicap
import Image
import numpy as np

from fonctions import *
from math import *

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

mov = INIT_MOV()
mov.open()

cam = d.Camera()
cam.open()

test_expo = 0.5

#----Valeur a changer par increment ou manuellement--------------

PAS = 0.0001
INTERVAL = 0.03
STEP = 2

#----------------------------------------------------------------

for i in range(0, STEP):
    VKE(mov, cam, interval = INTERVAL, pas = PAS, expo = test_expo, trou = "5micron", signe = 1)
    VKE(mov, cam, interval = INTERVAL, pas = PAS, expo = test_expo, trou = "5micron", signe = -1)
    VKE(mov, cam, interval = INTERVAL, pas = PAS, expo = test_expo, trou = "5micron", signe = 1)

    PAS += 0
    INTERVAL +=0 
