# Fonctions pour faire le focus et manipuler des images, prise de donnees et analyses

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
from math import *

import lsst.testbench.pollux.xyz as xyz
import lsst.testbench.dmk41au02as as d

test_expo = 0.5

def INIT_MOV():
    mov = xyz.XYZ()

    mov.x_port = '/dev/ttyUSB9'
    mov.y_port = '/dev/ttyUSB10'
    mov.z_port = '/dev/ttyUSB11'

    return mov

def MOVE_TO_DEFAULT(mov):
    default = np.loadtxt("default_pos.data", comments = '#')

    xpos = default[0]
    ypos = default[1]
    zpos = default[2]

    mov.move(x=xpos,y=ypos,z=zpos)

def CUT(data, hauteur = 10, largeur = 10):
    ''' Coupe l'image pour ne garder qu'une region autour du maximum
    @param data: tableau de donnees a analyser
    @param hauteur: nombre de pixels au dessus et en dessous du point max
    @param largeur: nombre de pixels a gauche et a droite du pixel max

    '''

    temp_max = np.where(data==np.max(data))
    a, b = [temp_max[0][0], temp_max[1][0]]
    
    cuts = data[a - largeur:a + largeur, b - hauteur:b + hauteur]

    return cuts

def PF(data, max_i): # Obtient le flux dans les pixels voisin sous la forme [SUD,OUEST,EST,NORD]
    pixels_flux = [data[max_i[0] - 1][max_i[1]], data[max_i[0]][max_i[1] -1], data[max_i[0]][max_i[1] + 1], data[max_i[0] + 1][max_i[1]]]

    return pixels_flux

def PCF(data, max_i):
    pcf = data[max_i[0]][max_i[1]]
    
    return pcf

def RATIO(pixel_central_flux, pixels_flux, nb_flux):
    ratio = float(pixels_flux[nb_flux])/pixel_central_flux
    
    return ratio

def FOCUS(mov, cam, interval=0.005, pas=0.001, expo = test_expo, trou = "5micron", cut = "no"):
    ''' Fait le focus pour un interval, un pas et un trou donne.
    Attention : moteurs et camera doivent etre initialises@param mov: nom des moteurs
    @param mov: nom des moteurs
    @param cam: nom de la camera
    @param interval: autour d'un point d'origine, distance avant et apres ce point sur laquelle travailler
    @param pas: pas de prise d'image, doit etre inferieur a interval
    @param trou: trou de travail
    @param expo: temps d'exposition desire
    '''
    borne = int(interval/pas)

    print("Attention : voulez vous supprimer le contenu de ./focus (yes = 1/no = 0) ? : ")
    suppr = input()

    if suppr == 1:
        commande = "rm -f ./focus/*.fits"
        os.system(commande)

    mov.move(dy=-interval)
    
    for i in range(0,2*borne):

        XPOS = mov.x_axis.get_position()
        YPOS = mov.y_axis.get_position()
        ZPOS = mov.z_axis.get_position()

        h = py.Header()
        
        mov.move(dy=pas)
        name = "./focus/" + str(time.time()) + "_" + trou 
        img = cam.capture(exposure = expo)
        
        img = np.array(img)
        temp_max = np.where(data==np.max(data))
        a, b = [temp_max[0][0], temp_max[1][0]]
        
        if cut == "yes":
            img = CUT(img)

        h.update('xpos', XPOS)
        h.update('ypos', YPOS)
        h.update('zpos', ZPOS)
        h.update('pos_pix_max_row', a)
        h.update('pos_pix_max_col', b)
        py.writeto(name + ".fits", img, header = h, clobber=True)

    mov.move(dy=-interval)

def VKE(mov, cam, interval = 0.05, pas = 0.0002, sens = "z", expo = test_expo, trou = "5micron", cut = "no"):
    '''Deplace le spot verticalement ou horizontalement, et prend une image a chaque pas
    @param mov: nom des moteurs
    @param cam: nom de la camera
    @param interval: distance sur laquelle faire l'aller et le retour en mm
    @param pas: division de l'interval de travail, doit etre inferieur a interval en mm
    @param sens: horizontal (x) ou vertical (z)
    @param trou: trou de travail
    @param expo: temps d'exposition desire en seconde
    '''
    borne = int(interval/pas)

    print("Attention : voulez vous supprimer le contenu de ./vke_beta (yes = 1/no = 0) ? : ")
    suppr = input()

    if suppr == 1:
        commande = "rm -f ./vke_beta/*.fits"
        os.system(commande)

    if sens == "z":
        for i in range(0,borne):

            h = py.Header()

            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()

            name = "./vke_beta/aller_z_" + str(time.time()) + "_z=" + str(ZPOS) + "_" + trou + "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)
            mov.move(dz=pas)
            
            img = np.array(img)
            if cut == "yes":
                img = CUT(img)

            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            py.writeto(name + ".fits", img, header = h, clobber=True)
        
        for i in range(0,borne):
 
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            mov.move(dz=-pas)
            
            name = "./vke_beta/retour_z_" + str(time.time()) + "_z=" + str(ZPOS) + "_" + trou + "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)

            img = np.array(img)
            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            py.writeto(name + ".fits", img, header = h, clobber=True)
    
    elif sens == "x":
        for i in range(0,borne):
 
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            name = "./vke_beta/aller_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou +  "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)
            
            mov.move(dx=pas)

            img = np.array(img)
            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            py.writeto(name + ".fits", img, header = h, clobber=True)
        
        for i in range(0,borne):
            
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            mov.move(dx=-pas)
            
            name = "./vke_beta/retour_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou + "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)
            
            img = np.array(img)
            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            py.writeto(name + ".fits", img, header = h, clobber=True)

def SAVE_RESULTS(position, flux, flux2, direc ="./results/", axe = "z", pas = "_0.1micron", dist = "_sur_20micron", trou = "_5micron", pose = "_0.1s", ext = ".res"):
    '''
    @param position:
    @param flux:
    @param flux2:
    @param direc:
    @param axe:
    @param pas:
    @param dist:
    @param trou:
    @param pose:
    @param ext:
    '''
    name = direc + axe + pas + dist + trou + pose + ext

    r = open(name, mode = "w")

    for i in range(0,len(position)):
        r.write(str(position[i]))
        r.write(" ")
        r.write(str(flux[i]))
        r.write(" ")
        r.write(str(flux2[i]))
        r.write("\n")

    r.close()

def READ_RESULTS(fichier):
    f = np.loadtxt(fichier)
    pos = f[:,0]
    flux = f[:,1]
    flux2 = f[:,2]

    plt.scatter(pos, flux, marker = '+', color = 'b')
    plt.scatter(pos, flux2, marker = '+', color = 'r')
    plt.xlabel("Position")
    plt.ylabel("Flux")
    plt.show()

def FOCUS_EQ_EST_OUEST(mov, cam, expo = test_expo, pas_raff = 0.0005, precision = 1.1, cut = "no"):
    data = cam.capture(exposure = expo)
    
    data = np.array(data)
    if cut == "yes":
        data = CUT(data)

    temp_max = np.where(data==np.max(data))
    max_i = [temp_max[0][0], temp_max[1][0]]

    pixels_flux = PF(data, max_i)
    pixel_central_flux = PCF(data, max_i)
    
    while((pixels_flux[1]/pixels_flux[2] > precision) or (pixels_flux[2]/pixels_flux[1] > precision)):
        if pixels_flux[1] > pixels_flux[2]:
            mov.move(dx=pas_raff) #Verifier le sens
        else:
            mov.move(dx=-pas_raff) #Verifier le sens
            
        temp_data = cam.capture(exposure = expo)
        temp_data = np.array(temp_data)
        if cut == "yes":
            temp_data = CUT(temp_data)


        pixels_flux = PF(temp_data, max_i)
        pixel_central_flux = PCF(temp_data, max_i)

    print "Fin de l'alignement horizontal"

def FOCUS_EQ_VERTICAL(mov, cam, expo = test_expo, pas_raff = 0.0005, precision = 1.1, cut = "no"):
    data = cam.capture(exposure = expo)

    data = np.array(data)
    if cut == "yes":
        data = CUT(data)

    temp_max = np.where(data==np.max(data))
    max_i = [temp_max[0][0], temp_max[1][0]]

    pixels_flux = PF(data, max_i)
    pixel_central_flux = PCF(data, max_i)
    
    while((pixel_central_flux/pixels_flux[3] > precision) or (pixels_flux[3]/pixel_central_flux > precision)):
        if pixel_central_flux > pixels_flux[3]:
            mov.move(dz=pas_raff) #Verifier le sens
        else:
            mov.move(dz=-pas_raff) #Verifier le sens
   
            temp_data = cam.capture(exposure = expo)
            temp_data = np.array(temp_data)

            if cut == "yes":
                temp_data = CUT(temp_data)
            
            pixels_flux = PF(temp_data, max_i)
            pixel_central_flux = PCF(temp_data, max_i)

    print "Fin de l'egalisation verticale"

def CHANGE_DEFAULT_POS(mov):
    print("Changer les positions par defaut du focus (yes = 1/no = 0) ? : ")
    suppr = input()

    if suppr == 1:
        commande = "rm -f ./default_pos.data"
        os.system(commande)
        
        pos = open("default_pos.data", "w")
        pos.write('# XPOS, YPOS, ZPOS')
        pos.write('\n')
        pos.write(str(mov.x_axis.get_position()) + " " + str(mov.y_axis.get_position()) + " " + str(mov.z_axis.get_position()))
        pos.close()

def INIT_IMAGES():
    fichiers = gl.glob("./focus/*fits")
    fichiers = sorted(fichiers)

    images = []
    for f in fichiers:
        images.append((py.open(f))[0])

    donnees = []
    for i in images:
        donnees.append(i.data)

    maxima = []
    for d in donnees:
        maxima.append(float(d.max()))
    maxima = np.array(maxima)

    sums = []
    for d in donnees:
        sums.append(float(d.sum()))
    sums = np.array(sums)

    ratios = maxima/sums
    
    temp_max = np.where(donnees[0]==np.max(donnees[0]))
    max_i = [temp_max[0][0], temp_max[1][0]]
    FLUX = []
    for d in donnees:
        FLUX.append([PCF(d, max_i), PF(d, max_i)])

    ratios_pix_sup_raff = []
    for F in FLUX:
        ratios_pix_sup_raff.append(RATIO(F[0], F[1], 3))
        
    return images, donnees, maxima, sums, ratios, ratios_pix_sup_raff

def analyse_vke(direc = "./vke_beta/*fits", pix1 = 3, pix2 = 4, axe = "z"):
    
    fichiers = gl.glob(direc)
    fichiers = sorted(fichiers)

    data = []
    x_pos = []
    y_pos = []
    z_pos = []

    for i in fichiers:
        temp = py.open(i)
        data.append(temp[0].data)
        x_pos.append(temp[0].header['XPOS'])
        y_pos.append(temp[0].header['YPOS'])
        z_pos.append(temp[0].header['ZPOS'])

    max_i = np.where(data[0]==np.max(data[0]))
    max_i = [max_i[0][0] - pix1, max_i[1][0]] #Pixel voision du pixel central

    max_i2 = np.where(data[0]==np.max(data[0]))
    max_i2 = [max_i2[0][0] - pix2, max_i2[1][0]]

    flux = []
    flux2 = []

    for d in data:
        flux.append(d[max_i[0]][max_i[1]])
        flux2.append(d[max_i2[0]][max_i2[1]])

    pas_deb = fichiers[1].find("0.")
    pas_fin = fichiers[1].find("mm")
    pas = fichiers[1][pas_deb:pas_fin + 2]

    #plt.scatter(position, flux, marker = '+', color = 'b')
    #plt.scatter(position, flux2, marker = '+', color = 'r')
    
    if axe == "z":
        pos = z_pos
    elif axe == "x":
        pos = x_pos
    elif axe == "y":
        pos = y_pos
        
    plt.scatter(pos[:len(flux)/2], flux[:len(flux)/2], marker = '+', color = 'b')
    plt.scatter(pos[:len(flux)/2], flux2[:len(flux)/2], marker = '+', color = 'r')
    plt.scatter(pos[len(flux)/2:], flux[len(flux)/2:], marker = '+', color = 'green')
    plt.scatter(pos[len(flux)/2:], flux2[len(flux)/2:], marker = '+', color = 'violet')
    plt.xlabel("Position")
    plt.ylabel("Flux")
    plt.title("Step of " + pas)
    plt.show()


def take(cam, expo= test_expo):
    cam.capture_and_save(exposure = expo, filename = "take", filetype = "FITS")
    
    commande = "ds9 take.fits" 
    os.system(commande)
