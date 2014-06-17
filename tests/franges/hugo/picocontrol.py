#!/usr/bin/env python
import sys
import os, os.path
import time, datetime
import math as m
import numpy as np
import pylab as pb
import pyfits
import scipy.ndimage as scind
import lsst.testbench.picomotor as pico
import lsst.testbench.dmk41au02as as d
import ds9
#--------------------------------------
#fonction calcul de la FFT 2D et rearrangement de la FFT  
#option echelle log ,suppression moyenne et convolution gaussienne
def fft_2(L, remove_mean=True,convolve=True,mask=True): 
    u = np.shape(L)[0]
    v = np.shape(L)[1]
    if remove_mean:
        L = np.array(L, dtype="float")
        L = L - L.mean()
    FFTL = np.abs(np.fft.fft2(L))
    FFTL = np.vstack( [FFTL[u/2:,:], FFTL[0:u/2,:]]) 
    FFTL = np.hstack( [FFTL[:,v/2:], FFTL[:,0:v/2]])
    if convolve:
        sigma = 2.1               #definition du sigma de la gaussienne 
        x = np.arange(-2,3)
        x = np.array([x])
        y = x.transpose()
        G = np.exp(-(x**2+y**2)/(2*sigma**2))
        FFTL = scind.convolve(FFTL, G, mode='constant', cval=0.0)

    if mask:
        uu = np.array([np.arange(u) - u/2]).transpose()
        vv = np.array([np.arange(v) - v/2])
        r2 = uu**2 + vv**2
        print r2.shape
        print FFTL.shape
        FFTL[r2 < 10**2] = 0
    
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
    """
    Calcule interfrange et orientation des franges
    a partir de l'image M
    """
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
    if ( alpha<np.arctan(float(v)/u)) :
        quant = m.sqrt((u*m.cos(alpha))**2+(u*m.tan(alpha))**2)
    else : 
        quant = m.sqrt((v*m.sin(alpha))**2+(v/m.tan(alpha))**2)
    posx_1 = quant*m.cos(alpha)/i
    posy_1 = quant*m.sin(alpha)/i
    return (posx_1,posy_1)
#------------------------------------------------
#fonction ouverture moteur
def mot_open():
    mot = pico.Picomotor(host="134.158.154.199")
    mot.open()
    return mot
#------------------------------------------------
#fonction ouvrant ds9 avec deux fenetre 'frame 1' et 'frame 2'
def ini_ds9() : 
    d = ds9.ds9()
    #d.set('width 1280')
    #d.set('height 1024')
    d.set('tile')
    d.set('frame 2')
    return d
#-------------------------------------------------
def pointeur(x, y, cursor='circle'): #b pour box et c pour cercle
  if cursor == 'circle': 
      d.set('region command {circle x y 25}')
  else:
      d.set('region command {box x y 25 25}')

# -----------------------------------------------------------------

def move_mirror(motor, driver, dx, dy):
    """
    Mouvement effectue avec compensation (le centre de
    gravite du miroir reste immobile).
    """
    dxc =   dx/2 - dy/2
    dyc = - dx/2 + dy/2
    ddc = - dx/2 - dy/2

    channels = {'x': 0, 'y': 2, 'd': 1}

    motor.move(driver, channels['x'], dxc, immediate = True)
    motor.move(driver, channels['y'], dyc, immediate = True)
    motor.move(driver, channels['d'], ddc, immediate = True)

# -----------------------------------------------------------------

def move_to_target(camera, motor, target_x, target_y):
    """
    Deplace les 3 moteurs pour attendre la cible
    dans l'espace de Fourier.
    """

    img = np.array(camera.capture(exposure = 0.001), dtype = "float")
    fftcimg = fft_2(img,1,1)
    (x1,y1,x2,y2) = max_pos(fftcimg)

    print "Target ", target_x, target_y
    print "Peak:  ", x1, y1, x2, y2

    scale = 10.0
    dx = int(scale * (target_x - x1))
    dy = int(scale * (target_y - y1))

    move_mirror(motor, "A1", dx, dy)

#--------------------------------------------------------------------------------


if len(sys.argv) < 3:
    print >>sys.stderr, "usage: picocontrol.py  <interfrange>  <angle>"
    sys.exit(1)

interfrange = float(sys.argv[1])
angle = float(sys.argv[2])


directory = "%s--%f--%f" % ( datetime.datetime.utcnow().isoformat(), interfrange, angle )
os.mkdir(directory)

u = 960
v = 1280
tx,ty = pos_fft(interfrange,angle,u,v)

print "Target = ", tx, ty

DS9 = ds9.ds9()
DS9.set("view info no")
DS9.set("view panner no")
DS9.set("view magnifier no")

#view  [layout horizontal|vertical]
#      [info yes|no]
#       [panner yes|no]
#       [magnifier yes|no]
#       [buttons yes|no]
#       [colorbar yes|no]
#       [colorbar horizontal|vertical]
#       [colorbar numerics yes|no]
#       [graph horizontal|vertical yes|no]
#       [filename yes|no[
#       [object yes|no]
#       [minmax yes|no]
#       [lowhigh yes|no]
#       [frame yes|no]
#       [image|physical|wcs|wcsa...wcsz yes|no]
#       [red yes|no]
#       [green yes|no]
#       [blue yes|no]

DS9.set('width 1280')
#DS9.set('height 1024')
DS9.set('tile')
DS9.set('frame 1')
DS9.set('zoom 0.5')
DS9.set('scale mode zscale')
DS9.set('frame 2')
DS9.set('zoom 2')
DS9.set('scale linear')
DS9.set('scale mode minmax')

motor = mot_open()
cam = camera()

exposure = 0.001

x1,y1 = 0, 0

while True:

    scale = 10.0
    dx = int(round(scale * (tx - x1)))
    dy = int(round(scale * (ty - y1)))

    if ( abs(dx) > 5000 ) or ( abs(dy) > 5000 ):
        print sys.stderr, "Warning: huge mirror movement !!! dx,dy = ", dx, dy
        sys.exit(2)

    move_mirror(motor, "A1", dx, dy)

    img = np.array(cam.capture(exposure = 0.001), dtype = "float")
    img -= img.mean()
    fftcimg = fft_2(img,1,1)
    (x1,y1,x2,y2) = max_pos(fftcimg)

    DS9.set('frame 1')
    DS9.set('cmap grey')
    DS9.set_np2arr(img)
    DS9.set('frame 2')
    DS9.set('cmap heat')
    DS9.set_np2arr(fftcimg)

    DS9.set('regions delete all')
    DS9.set('regions color red')
    DS9.set('regions command {box %d %d 5 5}' % (v/2+ty+1,u/2+tx+1))
    DS9.set('regions color green')
    DS9.set('regions command {circle %d %d 5}' % (v/2+y1+1,u/2+x1+1))

    t = time.time()
    DS9.set('frame 1')
    pngfilename = os.path.join(directory, "%f-frame.png" % t)
    DS9.set("export png %s" % pngfilename)
    DS9.set('frame 2')
    pngfilename = os.path.join(directory, "%f-fft.png" % t)
    DS9.set("export png %s" % pngfilename)

    os.system('xwd -name "SAOImage ds9" > /tmp/toto.xwd')
    os.system('convert /tmp/toto.xwd %s/%f-capture.png' % (directory, t))

    print "Target ", tx, ty
    print "Peak:  ", x1, y1, x2, y2

    dist = ((x1-tx)**2 + (y1-ty)**2)**.5
    print "Distance to target = ", dist

    print "Continue? Yes/No [Yes]"
    answer = raw_input()
    if answer.lower() == 'no':
        sys.exit(0)




    
# move_to_target(cam, motor, tx, ty)
