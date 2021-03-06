#Laurent, Hugo, Remy

import numpy as np
#import matplotlib.pyplot as plt
#import pyfits
import math as m
#import sys
#import ds9

def fft_2(L,b,p): #b pour echelle log/p suppression moyenne/g convolution
    #u = np.shape(L)[0]
    #v = np.shape(L)[1]
    cut = np.min(np.shape(L))
    L = L[:cut,:cut]
    if (p) : 
        L = L-L.mean()
    if (b) : 
        FFTL = np.log10(np.abs(np.fft.fft2(L)))
    else :
        FFTL = np.abs(np.fft.fft2(L))
    #FFTL = np.vstack( [FFTL[u/2:,:], FFTL[0:u/2,:]]) 
    #FFTL = np.hstack( [FFTL[:,v/2:], FFTL[:,0:v/2]]) #fft_shift ? np.angle()
    FFTL = np.fft.fftshift(FFTL)
    return FFTL

def max_pos(M) : # par rapport au centre
    u = np.shape(M)[0]
    v = np.shape(M)[1]
    maxi = np.max(M[:,v/2:])
    n = np.argmax(M[:,v/2:])
    posx_1 = 2*n/v
    posy_1 = v/2+n-posx_1*v/2 
    posx_1 = posx_1-u/2
    posx_2 = -posx_1   
    posy_1 = posy_1-v/2
    posy_2 = -posy_1
    return (maxi, posx_1, posy_1, posx_2, posy_2)

def int_ori(M):
    u = np.shape(M)[0]
    v = np.shape(M)[1]
    print (u,v)
    (maxi, posx_1, posy_1, posx_2, posy_2) =  max_pos(M)
    print  posx_2, posy_2
    alpha = m.atan2(float(posy_1),posx_1)
    #i = (u*v)/(u*posx_1*m.cos(alpha)+v*posy_1*m.sin(alpha))
    i = u/(np.sqrt(posy_1**2 + posx_1**2))
    alpha = np.degrees(alpha)
    print i, alpha
    return(i,alpha)



