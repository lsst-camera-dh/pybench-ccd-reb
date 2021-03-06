#Remy Le Breton
"""
Functions to analyse data : stack, unbias, flat_field...
In a directory, there should be three sub-directories :
bias, flats, fringes.
Doing merge_head_and_splice_frame enable to identify 
the instrument with the virtual instrument in telinst
(poloka-core) and split the frames to treat each channel
as a single CCD.
Tests are done with the test CCD, so not all the channels
are working, hence the "valid_ampl" argument in the 
"merge_head..." function.
"""


import os
import glob as gl
import numpy as np
import pyfits as pf

def merge_head_and_splice_frame(directory = "./", valid_ampl = [3,4,5,6,7,12,13,14,15,16]):
    """
    To do in the bias, flats and fringes directories.
    Merge header to be able to idendtify the intrument,
    and splice frame in order to only take the valid channels.
    """

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
    """
    To do in the bias directory.
    Make the master biases for all valid channels.
    """

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
    """
    To do in the flat or fringes directory.
    First, need to make merge_head... and do_medianstack
    in the bias directory in order to make the masterbiases
    """

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

def do_stacktwilights(directory = "./"):
    """
    To do in the flats/sorted_by_pos directory.
    Work on unbiased_amp_*.fits files.
    Make sure you have made sort_by_pos in the flats
    directory.
    Make the master flats for all valid channels.
    """
    
    pos = gl.glob("*")
    pos.sort()
    
    print pos
    print ""

    for p in pos:
        print "Computing position : " + p
        flats = gl.glob(p + "/*/unbiased_amp_*")
        flats.sort()
        
        flats_string = ""
        for f in flats:
            flats_string += f + " "

        os.system("stacktwilights " + flats_string)
        
        outs = gl.glob("CCD_*data.fits")
        outs.sort()
        souts = gl.glob("CCD_*sigma.fits")
        souts.sort()
        
        os.system("mkdir " + p + "/outs")
        os.system("mkdir " + p + "/souts")

        for o in outs:
            out_temp = pf.open(o)
            chan = (out_temp[0].header['EXTNAME'])
            chan = str(int(chan[chan.find("_") + 1 :]) + 1)
            if len(chan) == 1:
                chan = "0" + chan
            os.system("mv " + o + " " + p + "/outs/master_flat_amp_" + chan + ".fits")
            out_temp.close()

        for s in souts:
            sout_temp = pf.open(s)
            chan = (sout_temp[0].header['EXTNAME'])
            chan = str(int(chan[chan.find("_") + 1 :]) + 1)
            if len(chan) == 1:
                chan = "0" + chan
            os.system("mv " + s + " " + p + "/souts/sigma_master_flat_amp_" + chan + ".fits")
            out_temp.close()
    
def sort_by_pos(directory = "./"):
    """
    To do in the fringes directory.
    Sort image by pos and move unbiased data 
    in the sorted_by_pos directory
    """

    image_list = gl.glob(directory + "*fits")
    image_list.sort()

    positions = []

    for f in image_list:
        temp_pos = extract_pos(f)

        if len(positions) == 0:
            positions.append(temp_pos)

        if temp_pos not in positions:
            positions.append(temp_pos)

    os.system("mkdir sorted_by_pos")
    
    for p in positions:
        os.system("mkdir sorted_by_pos/" + p)

    for f in image_list:
        pos = extract_pos(f)
        unbiased_list = gl.glob(f[:-5] + "/unbiased_amp_*")
        unbiased_list.sort()
        os.system("mkdir " + " sorted_by_pos/" + pos + "/" + f[-23:-5])
        for u in unbiased_list:
            os.system("mv " + u + " sorted_by_pos/" + pos + "/" + u)

def flatfield(directory = "./"):
    """
    To do in the same directory as bias, flats and fringes.
    Flatfield the data images.
    Make sure the fringes has been unbias.
    Make sure sort_fringes_by_pos as been run.
    """

    os.chdir("flats/sorted_by_pos")
    mflat_pos_list = gl.glob("*")
    mflat_pos_list.sort()
    os.chdir("../../")
    
    os.chdir("fringes/sorted_by_pos")
    fringes_pos_list = gl.glob("*")
    fringes_pos_list.sort()
    os.chdir("../../")
   

    pos_to_compute = []
    for i in mflat_pos_list:
        if i in fringes_pos_list:
            pos_to_compute.append(i)
            
    print "Positions to compute are : "
    print pos_to_compute
    print ""

    nb_pos = len(pos_to_compute)
    i_pos = 1

    for p in pos_to_compute:
        flats = gl.glob(directory + "flats/sorted_by_pos/" + p + "/outs/master_flat_amp_*.fits")
        flats.sort()
        fringes = gl.glob(directory + "fringes/sorted_by_pos/" + p + "/*/*fits")
        fringes.sort()
        
        nb_fringes = len(fringes)
        i_fringes = 1

        #ave_skylevs = 0
        #for f in flats:
            #ffile = pf.open(f)
            #ave_skylevs += ffile[0].header['SKYLEV']
            #ffile.close()
        
        #ave_skylevs /= len(flats)
        
        #print ave_skylevs

        for f in flats:
            ffile = pf.open(f)
            
            same_amp = []
            for a in fringes:
                if a[-11:] == f[-11:]:
                    same_amp.append(a)

            fdata = ffile[0].data
            
            #skylev = ffile[0].header['SKYLEV']
            #norm_fdata = fdata/skylev
            norm_fdata = fdata

            for s in same_amp:
                print "Working on file : " + s[s.find("0x0020"):]
                print "Flatfield of amplifier : " + str(i_fringes) + "/" + str(nb_fringes)
                print "Position " + p + " : " + str(i_pos) + "/" + str(nb_pos)
                print ""

                sfile = pf.open(s)
                sdata = sfile[0].data
                flatfield_data = sdata #*ave_skylevs
                flatfield_data/=norm_fdata
                pf.writeto(s[:-20] + "flatfield_" + s[-11:], flatfield_data, header=sfile[0].header)
                sfile.close()
                i_fringes += 1

            ffile.close()

        i_pos += 1

def create_flat_slinks(directory = "./"):
    """
    To do in the same directory as bias, flats and fringes.
    Makes symbolic links in order to compare raw and flatfield
    data.
    """
    
    print "Creating masterflats symbolic links..."
    
    os.chdir(directory + "fringes/sorted_by_pos/")
    fringes_pos = gl.glob("*/")
    fringes_pos.sort()
    os.chdir("../../flats/sorted_by_pos/")
    flat_pos = gl.glob("*/")
    flat_pos.sort()
    os.chdir("../../")

    step_two_pos = []
    for i in fringes_pos:
        if i in flat_pos:
            step_two_pos.append(i[:-1])
        
    os.chdir("fringes/sorted_by_pos/")
    for t in step_two_pos:
        os.chdir(t)
        frames = gl.glob("*/")
        frames.sort()
        flats2 = gl.glob("../../../flats/sorted_by_pos/" + t + "/outs/master_flat_*.fits")
        flats2.sort()
        for f in frames:
            os.chdir(f)
            for flat in flats2:
                os.system("ln -s ../" + flat + " " + flat[-23:])
            os.chdir("../")
        os.chdir("../")
    os.chdir("../../")

def make_hdulist(keyword = "flatfield", output = "full_flatfield_image.fits"):
    """
    To do in the sorted_by_pos directory in the fringe directory
    Use this function to group all the image in one HDUList
    """
    frames = gl.glob("*/*/")
    frames.sort()
    length_f = len(frames)
    i_f = 1
    for f in frames:
        print "Computing frame : " + str(i_f) + "/" + str(length_f)
        images = gl.glob(f + keyword + "_amp_*.fits")
        images.sort()
        pri = pf.PrimaryHDU()
        hlist = pf.HDUList()
        hlist.append(pri)
        if len(images) != 0:
            for i in images:
                temp = pf.open(i)
                a = pf.CompImageHDU(temp[0].data, header = temp[0].header)
                hlist.append(a)
                temp.close()
    
            hlist.writeto(f + output)
        i_f +=1

def make_hdulist_data_and_flats():
    """
    To do in the sorted_by_pos directory in the fringe directory
    Use this function to group all the image in one HDUList for
    raw and flatfield data and masterflats at the same time.
    """
    print "Making hdu list for flatfield images..."
    make_hdulist(keyword = "flatfield", output = "full_flatfield_image.fits")
    print "Making hdu list for master_flat images..."
    make_hdulist(keyword = "master_flat", output = "full_masterflat_image.fits")
    print "Making hdu list for raw data images..."
    make_hdulist(keyword = "unbiased", output = "full_unbiased_image.fits")

def make_full_image(keyword = "flatfield", output = "single_flatfield_image.fits"):
    """
    To do in the sorted_by_pos directory in the fringe directory
    Use this function to group all the image in one fits image.
    """
    
    frames = gl.glob("*/*/")
    frames.sort()
    
    length_f = len(frames)
    i_f = 1
    for f in frames:
        print "Computing frame : " + str(i_f) + "/" + str(length_f)
        images = gl.glob(f + keyword + "_amp_*.fits")
        images.sort()

        if len(images) != 0:
            temp = pf.open(images[0])
            detsize = (temp[0]).header['DETSIZE']
            ytot, xtot = detsize.split(",")
            xtot = xtot.replace("]","")
            ytot = ytot.replace("[","")
            x1 = int(xtot.split(":")[1])
            y1 = int(ytot.split(":")[1])
            
            temp.close()
            
            total = np.zeros((x1,y1))
            for i in images:
                temp = pf.open(i)
                
                detsec = temp[0].header['DETSEC']
                ylen, xlen = detsec.split(",")
                xlen = xlen.replace("]","")
                ylen = ylen.replace("[","")
                x0, x1 = xlen.split(":")
                y0, y1 = ylen.split(":")
                if int(x0) < int(x1) and int(y0) > int(y1):
                    x0, x1 = int(x0) - 1, int(x1)
                    y0, y1 = int(y1) - 1, int(y0)
                    total[x0:x1,y0:y1] = temp[0].data[::,::-1]
                elif int(x0) > int(x1) and int(y0) < int(y1):
                    x0, x1 = int(x1) - 1, int(x0)
                    y0, y1 = int(y0) - 1, int(y1)
                    total[x0:x1,y0:y1] = temp[0].data[::-1,::]

                temp.close()
            pf.writeto(f + output, data = total[::,::-1], clobber = True)
        i_f +=1
        
def make_full_image_all():
    """
    To do in the sorted_by_pos directory in the fringe directory
    Use this function to group all the image in one fits image
    raw and flatfield data and masterflats at the same time.
    """
    print "Making image for flatfield images..."
    make_full_image(keyword = "flatfield", output = "single_flatfield_image.fits")
    print "Making image for master_flat images..."
    make_full_image(keyword = "master_flat", output = "single_masterflat_image.fits")
    print "Making image for raw data images..."
    make_full_image(keyword = "unbiased", output = "single_unbiased_image.fits")  

def make_dead_line(fact=3.):
    """
    To do in the sorted_by_pos directory in the fringe directory
    Make a boolean mask for data, masking line pattern. 
    To work on single_masterflat_image.fits.
    """
    frames = gl.glob("*/*/")
    frames.sort()
    
    length_f = len(frames)
    i_f = 1
    for f in frames:
        print "Computing frame : " + str(i_f) + "/" + str(length_f)
        image = gl.glob(f + "single_masterflat_image.fits")
        fringes = gl.glob(f + "single_flatfield_image.fits")
        if len(image) == 1 and len(fringes) == 1:
            mask = np.zeros((4004,4096))

            temp_fringes = pf.open(fringes[0])
            data = temp_fringes[0].data
            mask[data<0.] = 1
            temp_fringes.close()

            temp_flat = pf.open(image[0])
            d = temp_flat[0].data
            x_step = 143
            x_div = np.linspace(0,4004,29).astype(int)
            mask[d<0.00001] = 1
            d = np.ma.array(d,mask=mask)
            for x in x_div[:-1]:
                median = np.median(d[x:x+x_step,:])
                std = np.std(d[x:x+x_step,:])
                for i in range(4096):
                    col_median = np.median(d[x:x+x_step,i])
                    if np.fabs(col_median - median) > fact*std:
                        mask[x:x+x_step,i] = 1
            pf.writeto("mask.fits", mask, clobber = True)
            os.system("mv mask.fits " + f)
            temp_flat.close()
        i_f +=1
    

def extract_pos(fits, theta = False):
    """
    Read the position (XPOS, YPOS, ZPOS and THETAPOS
    if asked) of a header non-merged fits files in 
    the 'XYZ' extension.
    """
    
    temp = pf.open(fits)
    xpos = temp['XYZ'].header['XPOS']
    ypos = temp['XYZ'].header['YPOS']
    zpos = temp['XYZ'].header['ZPOS']
    
    if theta:
        tpos = temp['XYZ'].header['THETAPOS']
        temp_pos = str(xpos) + str(ypos) + str(zpos) + str(tpos)
    else:
        temp_pos = str(xpos) + str(ypos) + str(zpos)
    
    return temp_pos

def launch_pipeline(valid_ampl = [3,4,5,6,7,12,13,14,15,16]):
    """
    Launch the entire pipeline to obtain flatfielded images
    To be done in the main directory (in the same directory
    as bias/, flats/ and fringes/
    """

    direc = ["bias/", "flats/", "fringes/"]
    
    for d in direc:
        merge_head_and_splice_frame(directory = d, valid_ampl = valid_ampl)

    do_medianstack(directory = direc[0])
    
    for u in direc[1:]:
        do_unbias(directory = u)

    do_stacktwilights(directory = direc[1])
    #do_flat_medianstack(directory = direc[1])
    #put_masterflat_skylev_in_header(directory = direc[1] + "outs/")
    
    sort_fringes_by_pos(directory = direc[2])
    flatfield()
    create_flat_slinks()

#-------------------------------------------------------------
# Old functions

def do_flat_medianstack(directory = "./"):
    """
    To do in the flats directory.
    Work on unbiased_amp_*.fits files.
    Make the master flats for all valid channels.
    """
    frames = gl.glob("*/*/")
    frames.sort()
    length_f = len(frames)
    i_f = 1
    for f in frames:
        print "Computing frame : " + str(i_f) + "/" + str(length_f)
        images = gl.glob(f + keyword + "_amp_*.fits")
        images.sort()
        pri = pf.PrimaryHDU()
        hlist = pf.HDUList()
        hlist.append(pri)
        if len(images) != 0:
            for i in images:
                temp = pf.open(i)
                a = pf.CompImageHDU(temp[0].data, header = temp[0].header)
                hlist.append(a)
                temp.close()

    amp_list = gl.glob(directory + "*/unbiased*.fits")
    fits_list = gl.glob(directory + "*.fits")
    amp_list.sort()
    fits_list.sort()

    if len(amp_list) == 0:
        raise ValueError("Make sure you have run do_unbias")
    
    nb_images = len(fits_list)
    nb_amp = len(amp_list)/nb_images
    reference = amp_list[:nb_amp]
    remaining = amp_list[nb_amp:]

    positions = []

    for f in fits_list:
        temp_pos = extract_pos(f)

        if len(positions) == 0:
            positions.append(temp_pos)

        if temp_pos not in positions:
            positions.append(temp_pos)

    print positions

    os.system("mkdir outs")
    os.system("mkdir souts")
    
    for p in positions:
        os.system("mkdir outs/" + p)
        os.system("mkdir souts/" + p)
    
    for r in reference:
        same_amp = [r]
        im_amp = r[-11:]
        for t in remaining:
            im_amp_test = t[-11:]
            if (im_amp == im_amp_test):
                same_amp.append(t)

        for p in positions:
            same_amp_and_pos = []
            for sa in same_amp:
                temp_pos = extract_pos(sa[:-21] + ".fits")
                if temp_pos == p:
                    same_amp_and_pos.append(sa)

            
            string_same_amp_and_pos = ""
            for i in same_amp_and_pos:
                string_same_amp_and_pos += " " + i

            print string_same_amp_and_pos

            os.system("rawmedianstack -o master_flat_" + im_amp + " -s sout_" + im_amp + string_same_amp_and_pos)

            outs = gl.glob("master_flat*.fits")
            outs.sort()
            souts = gl.glob("sout*.fits")
            souts.sort()

            for o in outs:
                os.system("mv " + o + " " + directory + "outs/" + p)
            for s in souts:
                os.system("mv " + s + " " + directory + "souts/" + p)

def put_masterflat_skylev_in_header(directory="./"):
    """
    To do in the outs directory of the flats directory
    Write the skylev value in the fits files header,
    to be used in the flatfield.
    """
    pos_list = gl.glob(directory + "*")
    pos_list.sort()

    for p in pos_list:
        mflat_list = gl.glob(p + "/*fits")
        mflat_list.sort()
        
        string_mflat_list = ""
        for i in mflat_list:
            string_mflat_list += " " + i
        
        os.system("skylevinheader " + string_mflat_list)

def make_dead(fact=5.):
    """
    To do in the sorted_by_pos directory in the fringe directory
    Make a boolean mask for data. To work on single_masterflat_image.fits.
    """
    frames = gl.glob("*/*/")
    frames.sort()
    
    length_f = len(frames)
    i_f = 1
    for f in frames:
        print "Computing frame : " + str(i_f) + "/" + str(length_f)
        image = gl.glob(f + "single_masterflat_image.fits")
        if len(image) == 1:
            temp_flat = pf.open(image[0])
            d = temp_flat[0].data
            x_step = 143
            y_step = 128
            x_div = np.linspace(0,4004,29).astype(int)
            y_div = np.linspace(0,4096,33).astype(int)
            mask = np.zeros((4004,4096))
            for x in x_div[:-1]:
                for y in y_div[:-1]:
                    median = np.median(d[x:x+x_step,y:y+y_step])
                    std = np.std(d[x:x+x_step,y:y+y_step])
                    mask[x:x+x_step,y:y+y_step][np.fabs(d[x:x+x_step,y:y+y_step] - median) > fact*std] = 1
            pf.writeto("mask.fits", mask, clobber = True)
            os.system("mv mask.fits " + f)
            temp_flat.close()
        i_f +=1
