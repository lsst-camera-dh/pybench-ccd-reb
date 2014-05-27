#Pour le focus : prend des images le long de l'axe optique, et fit le spot en gaussien
#
#Raffinement du focus : 
#on test sur les pixels adjascents le ratio entre le flux du pixel central 
#et le leur. Si il est trop important, on se deplace dans la direction 
#opposee d'une fraction de pixel. On le fait pour plusieurs valeur de 
#ratio : 80%, 50%... jusqu'a une limite statisfaisante (10 % ?).
#
#
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

#--Raffinement-du-focus-------------------------

expo = O.O5

data = cam.capture(exposure = expo)
cuts = CUTS(data)

temp_max = np.where(cuts==np.max(cuts))
max_i = [temp_max[0][0], temp_max[1][0]]

pixels_flux = PF(cuts, max_i)
pixel_central_flux = PCF(cuts, max_i)

pas_raff = 0.0005

while((pixels_flux[1]/pixels_flux[2] > 1.1) or (pixels_flux[2]/pixels_flux[1] > 1.1)):
    if pixels_flux[1] > pixels_flux[2]:
        mov.move(dx=pas_raff)
    else:
        mov.move(dx=-pas_raff)

    temp_data = cam.capture(exposure = expo)
    temp_cuts = CUTS(temp_data)
    pixels_flux = PF(temp_cuts, max_i)
    pixel_central_flux = PCF(temp_cuts, max_i)


while((pixels_flux[0]p/ixels_flux[3] > 1.1) or (pixels_flux[3]p/ixels_flux[0] > 1.1)):
    if pixels_flux[0] > pixels_flux[3]:
        mov.move(dz=pas_raff)
    else:
        mov.move(dz=-pas_raff)
    
    temp_data = cam.capture(exposure = expo)
    temp_cuts = CUTS(temp_data)
    pixels_flux = PF(temp_cuts, max_i)
    pixel_central_flux = PCF(temp_cuts, max_i)
