#!/usr/local/bin/python2.7

import sys
import os
import glob
import time
import numpy as np
import pdb
import pyfits

#h = 512
h = 2020
#w = 512
w = 550
prescan = 10
maxscan = 256
numscan = h*w/(maxscan +1)

istart = 0
#iend = 7
iend = 15
#itotal = 8
itotal = 16
#headerpath = "/home/lsst/BNL_test_script/headers/"
headerpath = "/home/lsst/ccd_scripts/headers/"
imgpath = "/home/lsst/test_images/"

def extract_chan(num, in_arr):
	length = numscan * maxscan
        out_arr = in_arr[0:length,num]
        out_arr = out_arr.reshape(numscan,maxscan)
        return out_arr

def open_img(fp):
        dt = np.dtype('i4')
        buff = np.fromfile(fp, dtype=dt)
	#print buff[:100]
	#old: additional bits removed
        #buff = np.vectorize(lambda i: i | 0xfffc0000 if i & (1 << 17) else i & 0x0003ffff)(buff)
	#negative numbers still need to be translated 
	buff = np.vectorize(lambda i: i - 0x40000 if i & (1 << 17) else i )(buff)
	#print buff[:100]
        return buff

def print_stats(num, chan):
	print "Channel : ", num 
	print "max = {}  min = {}".format(np.max(chan),np.min(chan))
	print "average = {:.2f}  sigma = {:.2f}".format(np.mean(chan),np.std(chan))

def create_filename(fp):
	"""Creates name for new fits file with full path. Also outputs date of last access to file
	as a proxy for date of observation."""
	
	#output path depending on date of last change to file
	rootdir = "/home/lsst/test_frames/"
	timeobs = time.localtime(os.path.getctime(fp))
	filedate = time.strftime('%Y%m%d', timeobs)
	datedir = os.path.join(rootdir, filedate,'')
	if not os.path.isdir(datedir):
		#creates directory for that date
		os.mkdir(datedir)

	#builds output file name: number in directory _ ID number 
	#will overwrite instead of incrementing if file is already in directory
	allfiles = os.listdir(datedir)
	filenumber = 1
	newfileID = os.path.basename(fp).split('.')[0]
	for filename in allfiles:
		try:
			fileroot = filename.split('.')[0]
			(num, id) = fileroot.split('_')
		except:
			continue
		if id == newfileID:
			filenumber = int(num)
			break
		#find last number used if any, increments it
		if int(num) >= filenumber:
			filenumber = int(num)+1
			
	newfilename = "{}{:05d}_scan-{}.fits".format(datedir, filenumber, newfileID)

	return (newfilename, timeobs)

def read_header_file(headerfile, header):
	"""Reads some keywords and values from a dedicated text file into a header"""
	headerhdu = pyfits.Header.fromtextfile(headerfile)
	header.update(headerhdu)

def append_time_header(header, keyword, timeval):
	"""Appends a time value to the header as a formatted string under the given keyword."""
	header[keyword] = time.strftime("%Y-%m-%dT%H:%M:%S", timeval)

def create_fits(filename, headerlist):
	"""Creates fits file with primary HDU and adds header content from list of text files."""
	primaryhdu = pyfits.PrimaryHDU()
	primaryheader = primaryhdu.header
	for headername in headerlist:
		read_header_file(headername, primaryheader)
	#print primaryheader

	return primaryhdu
	
def extension_geometry(extheader, extnum):
	"""Appends geometry information into extension header.
	Adapted for scanning."""
	ihalf = itotal/2
	colwidth = maxscan
	extheader['DETSIZE'] = '[1:{},1:{}]'.format(ihalf*maxscan,2*numscan)
	extheader['DATASEC'] = '[1:{},1:{}]'.format(maxscan,numscan)

	#modified 02/05/2014 : correcting for real CCD geometry
	if extnum<ihalf:
		pdet = '1:{}'.format(numscan)
		#si = colwidth*(extnum+1)
		#sf = colwidth*extnum+1
		si = colwidth*extnum+1
		sf = colwidth*(extnum+1)
	else :
		pdet = '{}:{}'.format(numscan*2,numscan+1)
		#si = colwidth*(iend-extnum)+1
		#sf = colwidth*(iend-extnum+1)
		si = colwidth*(extnum-ihalf+1)
		sf = colwidth*(extnum-ihalf)+1

	extheader['DETSEC'] = '[{}:{},{}]'.format(si,sf,pdet)

def create_image_extension(imagearray, extheadername, extnum):
	"""Appends image data into an extension of the fits file"""

	#update(fitsfile, imagearray, header=extheader, ext=extnum)
	#compressed with RICE_1 by default
	#exthdu = pyfits.CompImageHDU(data=imagearray, name="CHAN_%d" % extnum)
	exthdu = pyfits.ImageHDU(data=imagearray, name="CHAN_%d" % extnum)
	#filling extension header
	extheader = exthdu.header
	read_header_file(extheadername, extheader)
	#print extheader
	extension_geometry(extheader, extnum)

	return exthdu

if __name__ == "__main__":
	
	cnt = 0

	filelist = []
	for i in range(len(sys.argv[:])-1):
		filelist.extend(glob.glob(imgpath+sys.argv[i+1]))

	#print filelist
	#FITS headers from different sources: local configuration, sequencer
	headerlist = [headerpath+"fitsheader.txt", headerpath+"localheader.txt"]

	for fp in filelist:
		cnt += 1
		sys.stdout.write("Processing img " + str(cnt) + "/" + str(len(filelist)) + " (" + str(fp) + ")\n")
		sys.stdout.flush()
		out = open_img(fp)

		#temporary solution to DAQ bug: complete missing data
		#missing = np.array([65536]*16)
		#out = np.append(out, missing)

		#reshape by channel here to save on operations
		length = out.shape[0]/itotal
		out = out.reshape(length, itotal)

		#output file
		(filename, timeobs) = create_filename(fp)
		primaryhdu = create_fits(filename, headerlist)
		append_time_header(primaryhdu.header, "DATE-OBS", timeobs)
		append_time_header(primaryhdu.header, "DATE", time.localtime())#this is only precise to the second
		hdulist = pyfits.HDUList([primaryhdu])

		for num in range(istart,iend+1) :
			chan = extract_chan(num, out)
       			print_stats(num, chan[1:-1])
			# Ds9 doesn't know int64 bits , convert it to float 32
			y = chan.astype(np.int32)

			#creates extension to fits file
			exthdu = create_image_extension(y, headerpath+"fitsextensionheader.txt", num)
			hdulist.append(exthdu)

		hdulist.writeto(filename, clobber=True)
		print "Done with "+filename
	sys.stdout.write(str(cnt) + " images read...\n")



