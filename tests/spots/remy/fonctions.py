# Fonctions pour faire le focus et manipuler des images
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

def CUT(data, hauteur = 25, largeur = 25):
    ''' Coupe l'image pour ne garder qu'une region autour du maximum
    @param data: tableau de donnees a analyser
    @param hauteur: nombre de pixels au dessus et en dessous du point max
    @param largeur: nombre de pixels a gauche et a droite du pixel max

    '''

    temp_max = np.where(data==np.max(data))
    a, b = [temp_max[0][0], temp_max[1][0]]
    
    cuts = data[a - largeur:a + largeur, b - hauteur:b + hauteur]

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

def FOCUS(mov, cam, interval=0.005, pas=0.001, expo = 0.005, trou = "20micron", cut = "no"):
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

        if cut == "yes":
            img = CUT(img)

        h.update('xpos', XPOS)
        h.update('ypos', YPOS)
        h.update('zpos', ZPOS)
        img.writeto(name + ".fits", header = h, clobber=True)


def VKE(mov, cam, interval = 0.02, pas = 0.0002, sens = "z", expo = 0.005, trou = "20micron", cut = "no"):
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

            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            img.writeto(name + ".fits", header = h, clobber=True)
        
        for i in range(0,borne):
 
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            mov.move(dz=-pas)
            
            name = "./vke_beta/retour_z_" + str(time.time()) + "_z=" + str(ZPOS) + "_" + trou + "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)

            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            img.writeto(name + ".fits", header = h, clobber=True)
    
    elif sens == "x":
        for i in range(0,borne):
 
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            name = "./vke_beta/aller_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou +  "_" + str(pas) + "mm"
            img = cam.capture_and_save(exposure = expo, filename = name, filetype = "FITS")
            
            mov.move(dx=pas)
            
            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            img.writeto(name + ".fits", header = h, clobber=True)
        
        for i in range(0,borne):
            
            h = py.Header()
            
            XPOS = mov.x_axis.get_position()
            YPOS = mov.y_axis.get_position()
            ZPOS = mov.z_axis.get_position()
            
            mov.move(dx=-pas)
            
            name = "./vke_beta/retour_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou + "_" + str(pas) + "mm"
            img = cam.capture(exposure = expo)
            
            if cut == "yes":
                img = CUT(img)
            
            h.update('xpos', XPOS)
            h.update('ypos', YPOS)
            h.update('zpos', ZPOS)
            img.writeto(name + ".fits", header = h, clobber=True)

def SAVE_RESULTS(position, flux, flux2, direc ="./results/", axe = "z", pas = "_0.1micron", dist = "_sur_20micron", trou = "_20micron", pose = "_0.005s", ext = ".res"):
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
