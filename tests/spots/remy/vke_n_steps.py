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

test_expo = 0.5

VKE(mov, cam, interval = 0.03, pas = 0.0001, expo = test_expo, trou = "5micron", signe = 1):
VKE(mov, cam, interval = 0.03, pas = 0.0001, expo = test_expo, trou = "5micron", signe = -1):
VKE(mov, cam, interval = 0.03, pas = 0.0001, expo = test_expo, trou = "5micron", signe = 1):
