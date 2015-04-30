#Remy Le Breton

import numpy as np
import glob as gl
import Image as im
import time
import serial
import pyfits as py

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
    step = hex(s)[2:]
    if (len(step) == 1) && s > 0:
        total = "000" + str(step)
        return total
    elif (len(step) == 2) && s > 0:
        total = "00" + str(step)
        return total
    elif (len(step) == 3) && s > 0:
        total = "0" + str(step)
        return total
    elif (len(step) == 1) && s < 0:
        total = "FFF" + str(step)
        return total
    elif (len(step) == 2) && s < 0:
        total = "FF" + str(step)
        return total
    elif (len(step) == 3) && s < 0:
        total = "F" + str(step)
        return total

#------------------------------------------------------
#Command list

ask_position_command = "C00000"
end_command = "/"
move_command = "44"

#------------------------------------------------------
cam = d.Camera()
cam.open()
expo = 0.033

for i in arduino.readlines():
    print i

init_position = launch_command(ask_position_command + end_command)
init_focus = cam.capture(exposure = expo)

init_var = compute_variance(init_focus)

init_steps = convert_steps_in_hex(50) #Init movement of 50 steps, then ask the position
init_move = move_command + init_steps + ask_position_command + end_command
move = init_move

for i in images:
    new_position = launch_command(arduino, move)

    img = cam.capture(exposure = expo)
    img = np.array(img)
    img_var = compute_variance(img)


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
