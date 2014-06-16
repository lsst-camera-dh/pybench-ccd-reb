import math as m
import numpy as np
import pylab as pb
import pyfits
import scipy.ndimage as scind
import lsst.testbench.picomotor as pico
import lsst.testbench.dmk41au02as as d
#import ds9
#--------------------------------------
#fonction calcul de la FFT 2D et rearrangement de la FFT  
#option echelle log ,suppression moyenne et convolution gaussienne
def fft_2(L,p,g): #p suppression moyenne/g convolution
    u = np.shape(L)[0]
    v = np.shape(L)[1]
    if (p) :
        L = np.array(L, dtype="float")
        L = L-L.mean()
    FFTL = np.abs(np.fft.fft2(L))
    FFTL = np.vstack( [FFTL[u/2:,:], FFTL[0:u/2,:]]) 
    FFTL = np.hstack( [FFTL[:,v/2:], FFTL[:,0:v/2]])
    if (g) :
        sigma = 2.1               #definition du sigma de la gaussienne 
        x = np.arange(-2,3)
        x = np.array([x])
        y = x.transpose()
        G = np.exp(-(x**2+y**2)/(2*sigma**2))
        FFTL = scind.convolve(FFTL, G, mode='constant', cval=0.0)
        return FFTL
    else : 
        return FFTL
#-------------------------------------------
#fonction de recherche des max et leurs positions
def max_pos(M) : # par rapport au centre
    u = np.shape(M)[0]
    v = np.shape(M)[1]
    n = np.argmax(M[:,v/2:])
    posx_1 = 2*n/v
    posy_1 = v/2+n-posx_1*v/2 
    posx_1 = posx_1-u/2
    posx_2 = -posx_1   
    posy_1 = posy_1-v/2
    posy_2 = -posy_1
    return (posx_1, posy_1, posx_2, posy_2)
#-------------------------------------------------
#fonction donnant interfrange et orientation
def int_ori(M):
    u = np.shape(M)[0]
    v = np.shape(M)[1]
    (posx_1, posy_1, posx_2, posy_2) =  max_pos(M)
    alpha = m.atan2(float(posy_1),posx_1)
    i = (u*v)/(u*posx_1*m.cos(alpha)+v*posy_1*m.sin(alpha))
    alpha = np.degrees(alpha)
    return(i,alpha)
#---------------------------------------------------
# fonction creation fichier fits 
def obs_ds9(M, nom) :
    f = pyfits.HDUList()
    img = pyfits.ImageHDU(M)
    f.append(img)
    f.writeto(nom, clobber=True)
#-----------------------------------------------------
#fonction donnant les donnees d'une image
def imp(nom) :
    f = pyfits.open(nom + ".fits")
    f[0].data
    img = f[0].data
    return img
#------------------------------------------------
#fonction ouverture de la camera : 
def camera():
    cam = d.Camera()
    cam.open()
    return cam
#-----------------------------------------------
#fonction donnant position en x et y des pics dans fft connaissant interfrange et orientation
#alpha en deg et entre 0 et 90 
def pos_fft(i,alpha,u,v) :
    alpha = np.radians(alpha)
    posx_1 = (u*v)/(i*m.cos(alpha)*(u+v))
    posy_1 = (u*v)/(i*m.sin(alpha)*(u+v))
    return (posx_1,posy_1)
#------------------------------------------------
#fonction ouverture moteur
def mot_open():
    mot = pico.Picomotor(host="134.158.154.199")
    mot.open()
    return mot
#------------------------------------------------
#fonction ouvrant ds9 avec deux fenetre 'frame 1' et 'frame 2'
#def ini_ds9() : 
#    d = ds9.ds9()
#    d.set('width 1280')
#    d.set('height 1024')
#   d.set('tile')
#   d.set('frame 2')
#   return d
#-------------------------------------------------
#def pointeur(x,y,b,c): #b pour box et c pour cercle
#   if (c) : 
#       d.set('region command {circle x y 25}')
#   if (b) :
#       d.set('region command {box x y 25 25}')
#------------------------------------------------
#fonction connaissant i et alpha bouge le moteur a la position de la figure d'interfrange
def pico_frange(i,alpha,precx,precy) : 
    mot = mot_open()
    cam = camera()
   # d = ini_ds9()
    u = 960
    v = 1280
    (posx_1,posy_1) = pos_fft(i,alpha,u,v)
    dx = posx_1-precx
    dy = posy_1-precy
    diag = int(np.minimum(dx,dy)/2.)
    if (np.minimum(dx,dy)==dx) :
        dxp = int(dx/2.)
        dyp = int(dy)
    else : 
        dyp = int(dy/2.)
        dxp = int(dx)
    comptdia = 0
    comptx = 0
    compty = 0
    while ( (comptdia < 500*diag) and (comptx < 500*(dxp-2)) and (compty < 500*(dyp-2))  ) :
        if ( comptdia + 500 > 500*diag):
            mot.select("A1",1)
            mot.send("REL A1 " + str(500*diag-comptdia) + " g" + mot.EOL)
            comptdia = comptdia +500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        elif(comptdia < 500*diag) :
            mot.select("A1",1)
            mot.send("REL A1 " + str(500) + " g" + mot.EOL)
            comptdia = comptdia +500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        if ( comptx + 500 > 500*(dxp-2)):
            mot.select("A1",0)
            mot.send("REL A1 " + str(500*(dxp-2)-comptx) + " g" + mot.EOL)
            comptx = comptx + 500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        elif(comptx < 500*(dxp-2)) :
            mot.select("A1",0)
            mot.send("REL A1 " + str(500) + " g" + mot.EOL)
            comptx = comptx + 500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        if ( compty + 500 > 500*(dy-2)):
            mot.select("A1",2)
            mot.send("REL A1 " + str(500*(dyp-2)-compty) + " g" + mot.EOL)
            compty = compty+500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        elif (compty < 500*(dyp-2)) :
            mot.select("A1",2)
            mot.send("REL A1 " + str(500) + " g" + mot.EOL)
            compty = compty +500
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
    if (int(dx) != int(posx_1)) :
        mot.select("A1",0)
        while ( int(dx)<int(posx_1)):
            mot.send("REL A1 100 g"+ mot.EOL)
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        while (int(dx)>int(posx_1)) : 
            mot.send("REL A1 -100 g" + mot.EOL)
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
    if (int(dy) != int(posy_1)) : 
        mot.select("A1",2)
        while ( int(dy)<int(posy_1)):
            mot.send("REL A1 100 g" + mot.EOL)
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
        while (int(dy)>int(posy_1)) : 
            mot.send("REL A1 -100 g" + mot.EOL)
            img = cam.capture(exposure = 0.001)
            #d.set('frame 1')
            #d.set_np2arr(img)
            fftcimg = fft_2(img,1,1)
            #d.set('frame 2')
            #d.set_np2arr(fftcimg)
            (dx,dy,x2,y2) = max_pos(fftcimg)
    cam.capture_and_save(exposure = 0.001, filename="frange_i-35_a-35", filetype="FITS")

#--------------------------------------------------------------------------------

i = 35
alpha = 35
pico_frange(i,alpha,0,0)

