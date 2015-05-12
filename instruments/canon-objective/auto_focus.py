#Remy Le Breton

import numpy as np
import glob as gl
import Image as im
import time
import serial
import pyfits as py
import xmlrpclib

#import lsst.instruments.dmk41au02as as d
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

arduino = serial.Serial('/dev/ttyACM0', 19200, timeout=1) 
time.sleep(5)

dmk_ready = input("Launch dmk /dev/video1 (no need to connect), press 1 when done : ")
camera = xmlrpclib.ServerProxy("http://localhost:8100/")
camera.connect()

default_exposure = 0.33 #ms
camera.setExposure(default_exposure)

origin = "middle" #to define and change if it is change. It is a variable to known where the origin (the 0) has been put.

print "default exposure is : " + str(default_exposure) + " " + "ms"

def ask_origin():
    print "Origin is at the : " + origin

def launch_command(arduino, code):
    arduino.write(code)
    time.sleep(len(code))
    return arduino.readlines()

def compute_variance(image):
    variance = np.var(image)
    variance = variance/((np.max(image) + np.min(image))**2)
    variance = np.sqrt(variance)
    return variance

def convert_steps_in_hex(s):
    if s > 0:
        step = hex(s)[2:]
        if (len(step) == 1):
            total = "000" + str(step)
            return total
        elif (len(step) == 2):
            total = "00" + str(step)
            return total
        elif (len(step) == 3):
            total = "0" + str(step)
            return total
    elif s < 0:    
        step = hex(65535 + s)[2:]
        return step

def take_and_show(camera):
    camera.photo()
    time.sleep(0.5)
    name = camera.save()
    time.sleep(0.5)
    to_show = im.open(name)
    to_show.show()

def take_and_load(camera):
    camera.photo()
    time.sleep(0.5)
    name = camera.save()
    time.sleep(0.5)
    tmp = im.open(name)
    return tmp

def take():
    camera.photo()
    time.sleep(0.5)
    name = camera.save()
    time.sleep(0.5)
    print "Photo taken at : " + name

#------------------------------------------------------
#Command list

ask_position_command = "C00000"
end_command = "/"
move_command = "44"

#------------------------------------------------------

for i in arduino.readlines():
    print i

init_position = launch_command(arduino, ask_position_command + end_command)

camera.photo()
time.sleep(0.5)
init_name = camera.save()
time.sleep(0.5)

init_focus = im.open(init_name)
init_focus = init_focus.getdata()
init_focus = np.array(init_focus)
init_var = compute_variance(init_focus)

init_steps = convert_steps_in_hex(50) #Init movement of 50 steps, then ask the position
init_move = move_command + init_steps + ask_position_command + end_command
move = init_move

for i in images:
    new_position = launch_command(arduino, move)

    pic = im.open(i) #pic.show() pic.size()
    d = pic.getdata()
    data = np.array(d)
    img_var = compute_variance(data)

#images = gl.glob("/home/rlebret/Documents/Data/Fringes/Test2_20150428/*.tif")
#images.sort()
#
#var = []
#
#for i in images:
#    pic = im.open(i)
#    d = pic.getdata()
#    data = np.array(d)
#    data_min = np.min(data)
#    data_max = np.max(data)
#    
#    variance = np.var(data)
#    variance = variance/((data_max + data_min)*(data_max + data_min))
#    variance = np.sqrt(variance)
#    
#    var.append(variance)
#
#var = np.array(var)
#focus = images[np.argmax(var)]
#
#print focus

#cam = d.Camera()
#cam.open()
#expo = 0.033

#init_focus = cam.capture(exposure = expo)

#img = cam.capture(exposure = expo)
#img = np.array(img)
#img_var = compute_variance(img)
