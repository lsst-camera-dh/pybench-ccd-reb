#Remy Le Breton

import numpy as np
#import glob as gl
#import Image as im
#import time
#import serial
import pyfits as pf
#import xmlrpclib
#import ds9
import matplotlib.pyplot as pl
#from scipy.optimize import curve_fit, fmin

#import lsst.testbench
#import lsst.testbench.scripts.ccd.functions

def delete_scans(img):
    scans = img.header['DATASEC']

    x1 = int(scans[(scans.find('[') + 1):scans.find(':')])
    x2 = int(scans[scans.find(':') + 1:scans.find(',')]) 
    y1 = int(scans[(scans.find(',') + 1):scans.find(':', scans.find(':') + 1)]) 
    y2 = int(scans[(scans.find(':', scans.find(':') + 1) + 1):scans.find(']')]) 
    
    x1 += 0
    x2 -= 1
    y1 += 0
    y2 -= 1

    return img.data[y1:y2,x1:x2]

def extract_scans(img):
    scans = img.header['DATASEC']

    x1 = int(scans[(scans.find('[') + 1):scans.find(':')])
    x2 = int(scans[scans.find(':') + 1:scans.find(',')]) 
    y1 = int(scans[(scans.find(',') + 1):scans.find(':', scans.find(':') + 1)]) 
    y2 = int(scans[(scans.find(':', scans.find(':') + 1) + 1):scans.find(']')]) 
    
    a = img.data[:,:x1-1]
    b = img.data[:,x2+1:]
    
    return a,b

def compute_variance(image):
    data = delete_scans(image)
    variance = np.var(data)
    variance = variance/((np.max(data) + np.min(data))**2)
    variance = np.sqrt(variance)
    return variance

def save_image(img):
    pos = B.xyz.position
    img[0].header['XPOS'] = (pos['x'], 'Position in mm on x-axis')
    img[0].header['YPOS'] = (pos['y'], 'Position in mm on y-axis')
    img[0].header['ZPOS'] = (pos['z'], 'Position in mm on z-axis')
    B.save_to_fits(img,meta)

def focus(state, expo = 1., epsilon = 10.,valid_ampli = [2,3,4]):

    if state == 'MIN':
        B.xyz.move({'x': 45,'y': 40,'z': 39.2})
    elif state == 'MAX':
        B.xyz.move({'x': 44 ,'y': 40,'z': 65.5 })
    elif state == 'OTHER':
        #Demander la position theorique en nombre de pas, et determiner le z0 par la fonction fitte
	print "To do"

    z0 = B.xyz.position['z']

    positions = np.linspace(z0 - epsilon, z0 + epsilon, 11)
    variances = []

    for z in positions:
        B.xyz.move({'z':z})
        meta = B.execute_reb_sequence('Acquisition', exptime=expo)
        img = B.conv_to_fits()
        var = 0
        for v in valid_ampli:
            var += compute_variance(img[v])
        variances.append(var)
        if save:
            save_image(img)

    focused, popt = fit_pol2(positions,variances)
    B.xyz.move({'z':focused})

def pol2(x,a,b,c):
    return a*x**2 + b*x + c

def fit_pol2(positions, variances):
    popt,popv = curve_fit(pol2,positions, variances)
    g = lambda x : -1*(popt[0]*x**2 + popt[1]*x + popt[2])
    x_min = fmin(g,positions[variances==np.max(variances)])
    return int(x_min*100)/100., popt

def init_data(n):
    img = pf.open("/home/rlebret/Documents/Data/Fringes/ccd_frames/20150713/0x0020150713120200.fits")
    i = img[n]
    idata = delete_scans(i)
    flat = pf.open("/home/rlebret/Documents/Data/Fringes/ccd_frames/20150713/0x0020150713122024.fits")
    f = flat[n]
    fdata = delete_scans(f)

    return idata, fdata

valid_chan = [3,4,5,6,7,12,13,14,15,16]

def channel_loop(channels = valid_chan):
    img = pf.open("/home/rlebret/Documents/Data/Fringes/ccd_frames/20150713/0x0020150713120200.fits")
    for i in channels:
        a, b = extract_scans(img[i])
        display(a,b)

def display(a,b):
    sa = np.shape(a)
    sb = np.shape(b)
    x = range(0,sa[0])
    
    ave_a = []
    ave_b = []
    
    for i in x:
        ave_a.append(np.average(a[i]))
        ave_b.append(np.average(b[i]))

    bins = 100

    pl.subplot(211)
    pl.title("Prescan")
    pl.hist(ave_a,bins = bins)

    pl.subplot(212)
    pl.title("Afterscan")
    pl.hist(ave_b,bins = bins)

    pl.figure()
    
    pl.subplot(211)
    pl.title("Prescan")
    pl.plot(x, ave_a)

    pl.subplot(212)
    pl.title("Afterscan")
    pl.plot(x, ave_b)

    pl.figure()

    pl.subplot(211)
    pl.title("Prescan")
    pl.plot(x,np.fft.fftshift(np.log10(np.abs(np.fft.fft(ave_a)))))

    pl.subplot(212)
    pl.title("Afterscan")
    pl.plot(x,np.fft.fftshift(np.log10(np.abs(np.fft.fft(ave_a)))))
    pl.show()
