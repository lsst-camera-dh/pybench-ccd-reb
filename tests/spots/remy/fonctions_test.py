#Pour tester les fonctions

import numpy as np
import pyfits as py

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
