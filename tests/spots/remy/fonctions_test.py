#Pour tester les fonctions

import numpy as np
import pyfits as py
import glob as gl


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

def analyse_vke(direc = "./vke_beta/*fits", pix1 = 3, pix2 = 4, axe = "z"):
    
    fichiers = gl.glob(direc)
    fichiers = sorted(fichiers)

    data = []
    x_pos = []
    y_pos = []
    z_pos = []

    for i in fichiers[:-1]:
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
    plt.scatter(pos[len(flux)/2:], flux[len(flux)/2:], marker = 'o', color = 'b')
    plt.scatter(pos[len(flux)/2:], flux2[len(flux)/2:], marker = 'o', color = 'r')
    plt.xlabel("Position")
    plt.ylabel("Flux")
    plt.title("Step of " + pas)
    plt.show()
