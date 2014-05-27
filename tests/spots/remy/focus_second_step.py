#Raffinement du focus : 
#on test sur les pixels adjascents le ratio entre le flux du pixel central 
#et le leur. Si il est trop important, on se deplace dans la direction 
#opposee d'une fraction de pixel. On le fait pour plusieurs valeur de 
#ratio : 80%, 50%... jusqu'a une limite statisfaisante (10 % ?).
#
#
# Par Remy Le Breton

import matplotlib.pyplot as plt
import pylab as py
import numpy as np
import scipy as sp
import sys
import os, os.path
import time
import math as m
import pyfits as py
import glob as gl
import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

#---Camera-et-moteurs-----------------------------------

#mov = xyz.XYZ()

#mov.x_port = '/dev/ttyUSB0'
#mov.y_port = '/dev/ttyUSB1'
#mov.z_port = '/dev/ttyUSB2'

#mov.open()

#cam = d.Camera()
#cam.open()

#--------------------------------------------------------

def CUTS(data):

    lines = np.shape(data)[0]
    rows = np.shape(data)[1]

    down = 15
    up = 17
    div = 30

    x_min_cut = down*rows/div
    y_min_cut = down*lines/div

    x_max_cut = up*rows/div
    y_max_cut = up*lines/div

    cuts = data[y_min_cut:y_max_cut,x_min_cut:x_max_cut]

    return cuts

def PF(cuts, max_i): # Obtient le flux dans les pixels voisin sous la forme [SUD,OUEST,EST,NORD]
    pixels_flux = [cuts[max_i[0] - 1][max_i[1]], cuts[max_i[0]][max_i[1] -1], cuts[max_i[0]][max_i[1] + 1], cuts[max_i[0] + 1][max_i[1]]]

    return pixels_flux

def PCF(cuts, max_i):
    pcf = cuts[max_i[0]][max_i[1]]
    
    return pcf

def RATIO(pixels_flux, nb_flux, pixel_central_flux):
    ratio = float(pixels_flux[3])/pixel_central_flux
    
    return ratio

#-----------------------------------------------------------------

data = cam.capture(exposure = 0.05)
cuts = CUTS(data)

max_i = np.where(cuts==np.max(cuts))
max_i = [max_i[0][0], max_i[1][0]]

pixels_flux = PF(cuts, max_i)
pixel_central_flux = PCF(cuts, max_i)

ratio = RATIO(pixels_flux, 3, pixel_central_flux)

pas = 0.0005

while ratio>0.2:
    mov.move(dz=pas)
    test = cam.capture(exposure = 0.05)
    test_cut = CUTS(test)
    test_pixels_flux = PF(test_cut, max_i)
    test_central_flux = PCF(test_cut, max_i)
    ratio = RATIO(test_pixels_flux, 3, test_central_flux)
