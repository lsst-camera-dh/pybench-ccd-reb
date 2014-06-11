import math as m
import numpy as np
import pylab as pb
import pyfits
import scipy.ndimage as scind
import lsst.testbench.picomotor as pico
import lsst.testbench.dmk41au02as as d
#--------------------------------------
#fonction calcul de la FFT 2D et rearrangement de la FFT  
#option echelle log ,suppression moyenne et convolution gaussienne
def fft_2(L,b,p,g): #b pour echelle log/p suppression moyenne/g convolution
    u = np.shape(L)[0]
    v = np.shape(L)[1]
    if (p) : 
        L = L-L.mean()
    if (b) : 
        FFTL = np.log10(np.abs(np.fft.fft2(L)))
    else :
        FFTL = np.abs(np.fft.fft2(L))
    FFTL = np.vstack( [FFTL[u/2:,:], FFTL[0:u/2,:]]) 
    FFTL = np.hstack( [FFTL[:,v/2:], FFTL[:,0:v/2]])
    if (g) :
        sigma = 2.1                            #definition du sigma de la gaussienne 
        x = np.arange(-2,3)
        x = np.array([x])
        y = x.transpose()
        G = np.exp(-(x**2+y**2)/(2*sigma**2))
        FFTLC = scind.convolve(M, G, mode='constant', cval=0.0)
        return FFTLC
    else : 
        return FFTL
#-------------------------------------------
#fonction de recherche des max et leurs positions
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
#-------------------------------------------------
#fonction donnant interfrange et orientation
def int_ori(M):
    u = np.shape(M)[0]
    v = np.shape(M)[1]
    print (u,v)
    (maxi, posx_1, posy_1, posx_2, posy_2) =  max_pos(M)
    print  posx_1, posy_1
    alpha = m.atan2(float(posy_1),posx_1)
    print alpha
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
    f = pyfits.open(nom)
    f[0].data
    img = f[0].data
    return img
#------------------------------------------------
fonction ouverture de la camera : 
def cam():
    camera = d.Camera()
    camera.open()
    return camera
#-----------------------------------------------
#fonction donnant position en x et y des pics dans fft connaissant interfrange et orientation
#alpha en deg et entre 0 et 90 °
def pos_fft(i,alpha,u,v) :
    alpha = np.radians(alpha)
    posx_1 = (u*v)/(i*m.cos(alpha)*(u+v))
    posy_1 = (u*v)/(i*m.sin(alpha)*(u+v))
    return (posx_1,posy_1)
#------------------------------------------------
#fonction ouverture moteur
def mot_open():
    mot = pico.picomotor()
    mot.open()
    return mot
#------------------------------------------------
#fonction connaissant i et alpha bouge le moteur a la position de la figure d'interfrange
def pico_frange(i,alpha,nom) : 
    mot = mot_open()
    cam = cam()
    u = 960
    v = 1280
    (posx_1,posy_1) = pos_fft(i,alpha,u,v)
    mot.select(A1,0)
    mot.send("REL A1 "500*posx_1"g" mot.EOL)
    mot.select(A1,2)
    mot.send("REL A2 "500*posy_1"g" mot.EOL)
    cam.capture_and_save(exposure = 0.001,filename = nom,filetype="FITS")
    img = imp(nom)
    fftcimg = fft_2(L,1,1,1)
    (maxi,x1,y1,x2,y2) = max_pos(fftcimg)
    if (x1!==posx_1) :
        mot.select(A1,0)
        while ( x1<posx_1):
             mot.send("REL A1 "100"g" mot.EOL)
             cam.capture_and_save(exposure = 0.001,filename = nom,filetype="FITS")
             img = imp(nom)
             fftcimg = fft_2(L,1,1,1)
             (maxi,x1,y1,x2,y2) = max_pos(fftcimg)
        while (x1>posx_1) : 
             mot.send("REL A1 "-100"g" mot.EOL)
             cam.capture_and_save(exposure = 0.001,filename = nom,filetype="FITS")
             img = imp(nom)
             fftcimg = fft_2(L,1,1,1)
             (maxi,x1,y1,x2,y2) = max_pos(fftcimg)
    if (y1!==posy_1) : 
        mot.select(A1,2)
        while ( y1<posy_1):
             mot.send("REL A1 "100"g" mot.EOL)
             cam.capture_and_save(exposure = 0.001,filename = nom,filetype="FITS")
             img = imp(nom)
             fftcimg = fft_2(L,1,1,1)
             (maxi,x1,y1,x2,y2) = max_pos(fftcimg)
        while (y1>posy_1) : 
             mot.send("REL A1 "-100"g" mot.EOL)
             cam.capture_and_save(exposure = 0.001,filename = nom,filetype="FITS")
             img = imp(nom)
             fftcimg = fft_2(L,1,1,1)
             (maxi,x1,y1,x2,y2) = max_pos(fftcimg)

#--------------------------------------------------------------------------------
#i = 35
#alpha = 35
#pico_frange(i,alpha,"test01recherchefrange")

