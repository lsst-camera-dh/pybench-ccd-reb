import os
import glob as gl

def splice_frame(directory = "./", valid_ampl = [3,4,5,13,14]):
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
    
    return fits_list

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
            
        os.system("rawmedianstack -o out_" + im_amp + " -s sout_" + im_amp + string_same_amp)

    os.system("mkdir outs")
    os.system("mkdir souts")

    outs = gl.glob("out*.fits")
    outs.sort()
    souts = gl.glob("sout*.fits")
    souts.sort()

    for o in outs:
        os.system("mv " + o + " " + directory + "outs/")
    for s in souts:
        os.system("mv " + s + " " + directory + "souts/")

