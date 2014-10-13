import sys
import os, os.path
import time

#import unicap
#import Image
import numpy as np
import pyfits as py
import scipy.optimize as opt
import pylab as pb
import glob as gl
import matplotlib.pyplot as plt

#from fonctions import *
from math import *

import lsst.instruments.pollux.xyz as xyz
#import lsst.instruments.dmk41au02as as d

mov = INIT_MOV()
mov.open()

#cam = d.Camera()
#cam.open()

