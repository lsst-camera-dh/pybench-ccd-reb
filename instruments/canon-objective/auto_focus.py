#Remy Le Breton

import numpy as np
import glob as gl
import Image as im
import time
import serial

#import lsst.instruments.dmk41au02as as d
#import pyfits as py
#cam = d.Camera()
#cam.open()
#name = "./focus_images/" + str(time.time())
#cam.capture_and_save(exposure = 0.033, filename = name, filetype = "FITS")
#img = cam.capture(exposure = expo)
#img = np.array(img)
#Img = py.open(name) Img[0].data
#Img.close()

#=====> See how to make the setup ?
#ser = serial.Serial('/dev/tty.usbserial', 19200) <=== mettre la bonne vitesse et nom
#time.sleep(1)
#ser.open() <== a priori pas besoin d'open
#ser.read()
#ser.write()
#while 1:
#code=input("instruction")
#ser.write(code)

images = gl.glob("./Test2_20150428/*.tif")
images.sort()

var = []

for i in images:
    pic = im.open(i)
    d = pic.getdata()
    data = np.array(d)
    data_min = np.min(data)
    data_max = np.max(data)
    
    variance = np.var(data)
    variance = variance/((data_max + data_min)*(data_max + data_min))
    variance = np.sqrt(variance)
    
    var.append(variance)

var = np.array(var)
focus = images[np.argmax(var)]

print focus

def open_arduino():
    ser = serial.Serial('/dev/ttyACM0', 19200, timeout=1) 
    time.sleep(5)

def launch_command():
    code = input("Instruction ? : ")
    ser.write(code)
    time.sleep(len(code))
    return ser.readlines()
    
