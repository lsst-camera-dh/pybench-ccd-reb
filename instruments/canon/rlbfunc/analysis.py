import os
import glob as gl
import numpy as np
import pyfits as pf

def merge_head_and_splice_frame(directory = "./", valid_ampl = [4,5,6,7,12,13,14,15,16]):
    fits_list = gl.glob(directory + "*.fits")
    fits_list.sort()
    for f in fits_list:
        im_dir = f[:-5] + "/"
        begin_name = f.find("0x")
        im_name = f[begin_name:-5] + ".fz"

        os.system("mkdir " + im_dir)
        os.system("merge_headers " + f + " -c -d " + im_dir)
        for v in valid_ampl:
            if len(str(v)) == 1:
                name = "0" + str(v)
            else:
                name = str(v)
            os.system("imcopy " + im_dir + im_name + "\[" + str(v) + "\] " + im_dir + "amp_" + name + ".fits")

def do_medianstack(directory = "./"):
    amp_list = gl.glob(directory + "*/*.fits")
    fits_list = gl.glob(directory + "*.fits")
    amp_list.sort()

    nb_images = len(fits_list)
    nb_amp = len(amp_list)/nb_images
    reference = amp_list[:nb_amp]
    remaining = amp_list[nb_amp:]

    for r in reference:
        same_amp = [r]
        im_amp = r[-11:]
        for t in remaining:
            im_amp_test = t[-11:]
            if im_amp == im_amp_test:
                same_amp.append(t)

        string_same_amp = ""
        for i in same_amp:
            string_same_amp += " " + i
        
        print string_same_amp
            
        os.system("rawmedianstack -o master_bias_" + im_amp + " -s sout_" + im_amp + string_same_amp)

    os.system("mkdir outs")
    os.system("mkdir souts")

    outs = gl.glob("master_bias*.fits")
    outs.sort()
    souts = gl.glob("sout*.fits")
    souts.sort()

    for o in outs:
        os.system("mv " + o + " " + directory + "outs/")
    for s in souts:
        os.system("mv " + s + " " + directory + "souts/")

def do_unbias(directory = "./"):
    amp_list = gl.glob(directory + "*/*.fits")
    mbias = gl.glob(directory + "../bias/outs/*.fits")
    fits_list = gl.glob(directory + "*.fits")
    amp_list.sort()
    mbias.sort()

    nb_images = len(fits_list)
    nb_amp = len(amp_list)/nb_images
    nb_mbias = len(mbias)
    reference = amp_list[:nb_amp]
    remaining = amp_list[nb_amp:]

    if nb_mbias != nb_amp:
        raise ValueError("The number of channel to work on is wrong")

    amp_list = np.reshape(amp_list, (nb_images,nb_amp))

    for image in amp_list:
        for num in range(0,nb_amp):
            out_name = "unbiased_" + image[num][-11:]
            dir_name = image[num][:-11]
            os.system("unbias -f " + str(image[num]) + " -b " + str(mbias[num]) + " -o " + out_name)
            temp = pf.open(out_name, mode = "update")
            datasec = temp[0].header['DATASEC']
            data_temp = datasec[1:-1].split(",")
            x = data_temp[0].split(':')
            y = data_temp[1].split(':')
            new_datasec = "[" + str(int(x[0])-10) + ":" + str(int(x[1])-10) + "," + y[0] + ":" + y[1] +"]"
            temp[0].header['DATASEC'] = new_datasec
            temp.writeto(out_name, clobber = True)
            temp.close()
            os.system("mv " + out_name + " " + dir_name)
        
    

def do_flat_medianstack(directory = "./"):
    amp_list = gl.glob(directory + "*/unbiased*.fits")
    fits_list = gl.glob(directory + "*.fits")
    amp_list.sort()
    fits_list.sort()

    nb_images = len(fits_list)
    nb_amp = len(amp_list)/nb_images
    reference = amp_list[:nb_amp]
    remaining = amp_list[nb_amp:]

    positions = []

    for f in fits_list:
        temp = pf.open(f)
        xpos = temp['XYZ'].header['XPOS']
        ypos = temp['XYZ'].header['YPOS']
        zpos = temp['XYZ'].header['ZPOS']
        #tpos = temp['XYZ'].header['TPOS']
        
        temp_pos = str(xpos) + str(ypos) + str(zpos) # + str(tpos)

        if len(positions) == 0:
            positions.append(temp_pos)

        if temp_pos not in positions:
            positions.append(temp_pos)
            
        temp.close()

    print positions

    for r in reference:
        same_amp = [r]
        im_amp = r[-11:]
        for t in remaining:
            im_amp_test = t[-11:]
            if im_amp == im_amp_test:
                same_amp.append(t)

        string_same_amp = ""
        for i in same_amp:
            string_same_amp += " " + i
        
        print string_same_amp
            
        os.system("rawmedianstack -o master_flat_" + im_amp + " -s sout_" + im_amp + string_same_amp)

    os.system("mkdir outs")
    os.system("mkdir souts")

    outs = gl.glob("master_flat*.fits")
    outs.sort()
    souts = gl.glob("sout*.fits")
    souts.sort()

    for o in outs:
        os.system("mv " + o + " " + directory + "outs/")
    for s in souts:
        os.system("mv " + s + " " + directory + "souts/")
