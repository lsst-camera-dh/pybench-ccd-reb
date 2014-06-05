#Pour tester les fonctions

import numpy as np


def CUTS(data, hauteur = 200, largeur = 200): #On coupe l'image pour ne garder que la region autour du point max

    temp_max = np.where(data==np.max(data))
    max_i = [temp_max[0][0], temp_max[1][0]]

    cuts = data[y_min_cut:y_max_cut,x_min_cut:x_max_cut]

    return cuts
