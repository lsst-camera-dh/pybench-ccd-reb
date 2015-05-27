#Remy Le Breton

import numpy as np
import glob as gl
import Image as im
import time
import serial
import pyfits
import xmlrpclib
import ds9
import matplotlib.pyplot as plt

INIT_STEP = 200


arduino = serial.Serial('/dev/ttyACM0', 19200, timeout=1) 
time.sleep(5)

dmk_ready = input("Launch dmk /dev/video1 (no need to connect), press 1 when done : ")
camera = xmlrpclib.ServerProxy("http://localhost:8100/")
camera.connect()

default_exposure = 100.0 #33.3 #ms
camera.setExposure(default_exposure)

print "default exposure is : " + str(default_exposure) + " " + "ms"

def setExpoTime(camera, t):
    camera.setExposure(t)

def launch_command(arduino, code):
    arduino.write(code)
    time.sleep(len(code))
    line = arduino.readlines()
    for i in range(len(line)):
        line[i] = line[i].replace("\r\n","")
    return line

def compute_variance(image):
    variance = np.var(image)
    variance = variance/((np.max(image) + np.min(image))**2)
    variance = np.sqrt(variance)
    return variance

def convert_steps_in_hex(s):
    if s >= 0:
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
    viewer = ds9.ds9()
    to_show = im.open(name)
    viewer.set_np2arr(np.array(to_show))

def show(image):
    viewer = ds9.ds9()
    viewer.set_np2arr(image)

def take_and_load(camera):
    camera.photo()
    time.sleep(0.5)
    name = camera.save()
    #time.sleep(0.5)
    tmp = im.open(name)
    return np.array(tmp)

def take_same_many(camera, N):
    images = []
    for i in range(N):
        camera.photo()
        time.sleep(0.5)
        name = camera.save()
        time.sleep(0.5)
        images.append(np.array(im.open(name)))
    return images

def take(camera):
    camera.photo()
    time.sleep(0.5)
    name = camera.save()
    time.sleep(0.5)
    print "Photo taken at : " + name

def extract_position(lines):
    line = lines[(lines.index([i for i in lines if 'C0' in i][0]) + 1):]
    for i in range(len(line)):
        pos = line[i].find(" ")
        line[i] = line[i][pos+1:]
        line[i] = line[i][-2:]
    
    position = line[0] + line[1]

    return position

def init_auto_focus(arduino,camera):
    images = []
    test_pos = []
    max_pos = []
    theo_mov = []
    variances = []
    step = INIT_STEP
    position = step
    sign = 1
    first = 1

    print "Initialization of auto-focus"

    temp = extract_position(launch_command(arduino, "0G060HC00000/"))
    images.append(take_and_load(camera))
    test_pos.append(temp)
    max_pos.append(temp)
    theo_mov.append(0)
    variances.append(compute_variance(images[0]))

    nb_steps = 20 #900//step

    for i in range(nb_steps):
        max_pos.append(extract_position(launch_command(arduino, "0G060HC00000/")))
        test_pos.append(extract_position(launch_command(arduino, "0G44" + convert_steps_in_hex(position) + "0HC00000/")))
        images.append(take_and_load(camera))
        variances.append(compute_variance(images[i+1]))
        theo_mov.append(position)

        print "Step " + str(i) + "/" + str(nb_steps - 1) + " at relative " + str(position) + " and variance = "+ str(variances[i+1])

        if first:
            if (variances[i+1] < variances[i]) and (abs(variances[i+1]/variances[i]) > 0.25):
                step = step//2
                sign = -1*sign
                step = sign*step
                first = 0
        else:
            if (variances[i+1] < variances[i]):
                step = step//2
                sign = -1*sign
                step = sign*step

        position += step
        if abs(step) < 20:
            print "Step < 20, stop"
            break
        elif position > 900:
            print "Position > 900, stop"
            break
        elif i == (nb_steps - 1):
            print "Have reached the maximum number of step"

    return images, test_pos, theo_mov, max_pos, variances

def save_images_fits(images):
    name = input("Directory name (date int) ? : ")
    for i in images:
        pyfits.writeto("/home/rlebret/Documents/Data/Fringes/" + str(name) + "/" + str(int(time.time())) + ".fits", i)
        time.sleep(1.5)

#------------------------------------------------------

for i in arduino.readlines():
    
    print i

images, images_pos, theo_mov, max_pos, variances = init_auto_focus(arduino, camera)

plt.plot(range(len(variances)),variances)
plt.show()

max_index = variances.index(np.max(variances))
pos_var_max = theo_mov[max_index]

print "The final position for focus is : ", pos_var_max

launch_command(arduino, "0G44" + convert_steps_in_hex(pos_var_max) + "0H/")
    
