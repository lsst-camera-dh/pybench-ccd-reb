#Pour le focus : prend des images le long de l'axe optique, et fit le spot en gaussien
#
#Raffinement du focus : 
#On teste sur les pixels adjacents [SUD,OUEST,EST,NORD] le ratio OUEST/EST et SUD/NORD.
#On veut que les deux soient proches de 1. Quand les deux sont proches de 1, le spot est centré.
#
#Par Remy Le Breton

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits
import scipy.optimize as opt
import pylab as pb

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d
#--------------------------------------------------------

def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    data = data + 0.0000000000000001
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    col_sum = col.sum()

    if col_sum == 0:
        col_sum = 0.00000000000000001

    width_x = sqrt(abs((np.arange(col.size)-y)**2*col).sum()/col_sum)
    row = data[int(x), :]
    row_sum = row.sum()

    if row_sum == 0:
        row_sum = 0.00000000000000001

    width_y = sqrt(abs((np.arange(row.size)-x)**2*row).sum()/row_sum)
    height = data.max()
    return height, x, y, width_x, width_y

def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: ravel(gaussian(*p)(*np.indices(data.shape)) - data)
    p, success = opt.optimize.leastsq(errorfunction, params)
    return p

def CUTS(data): #On coupe l'image pour ne garder que la region central

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

print("Attention : voulez vous supprimer le contenu de ./focus (y/n) ? : ")
suppr = input()

if suppr == 'y':
    commande = "rm -f ./focus/*.fits"
    os.system(commande)

mov.move(dy=-interval)

trou = "20micron"

for i in range(0,2*borne):

    XPOS = mov.x_axis.get_position()

    mov.move(dy=pas)
    name = "./focus/" + str(time.time()) + "_" + trou 
    cam.capture_and_save(exposure = 0.1, filename = name, filetype = "FITS")

    update = py.open(name)
    update[0].header.update('xpos', XPOS)
    update.close()

fichiers = gl.glob("./focus/*.fits")
fichiers = sorted(fichiers)

donnees = []

for i in fichiers:
    donnees.append((py.open(i))[0].data)

params = []
fit = []

for i in cuts:
    matshow(i, cmap=cm.gist_earth_r)
    plt.xlim(30,50)
    plt.ylim(30,40)

    param_i = fitgaussian(i)
    params.append(param_i)

    fit_i = gaussian(*param_i)
    fit.append(fit_i)

    contour(fit_i(*indices(i.shape)), cmap=cm.copper)
    ax = gca()
    (height, x, y, width_x, width_y) = param_i

    text(0.95, 0.05, """
       x : %.1f
       y : %.1f
       width_x : %.1f
       width_y : %.1f""" %(x, y, width_x, width_y),
         fontsize=16, horizontalalignment='right',
         verticalalignment='bottom', transform=ax.transAxes)

    show()

#
#
# Selectioner l'image ou le spot est le plus petit, et ce mettre a cette position
#
#

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


while((pixels_flux[0]/pixels_flux[3] > 1.1) or (pixels_flux[3]/pixels_flux[0] > 1.1)):
    if pixels_flux[0] > pixels_flux[3]:
        mov.move(dz=pas_raff)
    else:
        mov.move(dz=-pas_raff)
    
    temp_data = cam.capture(exposure = expo)
    temp_cuts = CUTS(temp_data)
    pixels_flux = PF(temp_cuts, max_i)
    pixel_central_flux = PCF(temp_cuts, max_i)
