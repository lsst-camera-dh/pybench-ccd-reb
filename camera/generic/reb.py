#
# LSST / LPNHE
# Author: Claire Juramy, Laurent Le Guillou
#
"""
Generic REB object. The specific details for each board should be
added in their specific object. In particular this does not talk
to any FPGA at all.
"""
import time
import os
import numpy as N
import pyfits

def generate_tag(number):
    today = time.gmtime()
    tagstr = time.strftime('%Y%m%d', today)+'%05d' % number
    tag = int(tagstr,16)
    return tag

def get_sequencer_hdu(seq):
    """
    Builds table HDU for FITS file containing sequencer dump
        :param seq: Sequencer
        :return: pyfits.TableHDU
        """
    prog = seq.program
    progaddr = prog.instructions.keys()
    prognum = 256 + len(progaddr)

    slicenum = N.ndarray(shape=(prognum,), dtype=N.dtype('a4'))
    output = N.ndarray(shape=(prognum,), dtype=N.dtype('a32'))
    duration = N.ndarray(shape=(prognum,), dtype=N.dtype('i8'))

    for ifunc in seq.functions.iterkeys():
        func = seq.get_function(ifunc)
        for islice in func.outputs.keys():
            i = ifunc * 16 + islice
            slicenum[i] = hex(i)[2:]
            output[i] = bin(func.outputs[islice])[2:]
            duration[i] = func.timelengths[islice]

    for i, addr in enumerate(sorted(progaddr)):
        slicenum[i+256] = '30' + hex(addr)[2:]
        output[i+256] = prog.instructions[addr].__repr__()[:20]
        duration[i+256] = prog.instructions[addr].repeat

    slicecol = pyfits.Column(name="Address", format='A4', array=slicenum)
    outputcol = pyfits.Column(name="Output", format='A32', array=output)
    durationcol = pyfits.Column(name="Time", format='I8', array=duration)

    exthdu = pyfits.new_table([slicecol, outputcol, durationcol], tbtype='TableHDU')
    # add name to extension here
    exthdu.header["EXTNAME"] = "SEQ_CFG"

    return exthdu
# =======================================================================

class REB(object):
    xmlfile = "sequencer-soi.xml"
    rawimgdir = "/data/raw/"
    fitstopdir = "/data/frames/"
    imgtag = 0
    stripes = [0]
    nchannels = 16
    # to be loaded from XML later
    imglines = 2020
    imgcols = 550
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
    min_exposure = int(0.1 / exposure_unit)  # minimal shutter opening time (not used for darks)

    # ===================================================================

    def __init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0]):
        self.seq = None  # will be filled when loading the sequencer

    def get_exposure_time(self, darktime=False):
        """
        Gets the exposure time from the subroutines in memory.
        (input in seconds). If darktime is set to true, gives the dark 'exposure' time instead.
        :param darktime: boolean
        """

        # look up address of exposure subroutine
        # then get current instruction
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            instruction = self.seq.program.instructions[darkadd]
        else:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            instruction = self.seq.program.instructions[exposureadd]
        iter = instruction.repeat

        return float(iter) * self.exposure_unit  # in seconds

    # --------------------------------------------------------------------

    def conv_to_fits(self, imgname, channels=None):
        """
        Creates the fits object from the acquired data.
        """

        # Reading raw file to array
        dt = N.dtype('i4')
        buff = N.fromfile(imgname, dtype=dt)

        # for 18-bit data:
        # negative numbers are translated, sign is inverted on all data, also make all values positive
        # 0 -> 1FFFF, 1FFFF -> 0, 20000 -> 3FFFF, 3FFFF -> 20000
        rawdata = N.choose(buff & 0x20000, (0x1ffff-buff, 0x5ffff-buff))
        # reshape by channel
        length = self.imglines * self.imgcols
        rawdata = rawdata.reshape(length, self.nchannels)

        # Creating FITS HDUs:
        # Create empty primary HDU and fills header
        primaryhdu = pyfits.PrimaryHDU()
        # Create HDU list
        hdulist = pyfits.HDUList([primaryhdu])

        # Add extensions for channels HDUs
        for num in range(self.nchannels):
            if channels:  # to skip non-useful channels
                if num not in channels:
                    continue
            chan = rawdata[0:length,num]
            chan = chan.reshape(self.imglines, self.imgcols)
            y = chan.astype(N.int32)
            # create extension to fits file for each channel
            exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
            # exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
            self.get_extension_header(num, exthdu)
            avchan = N.mean(y[11:self.imgcols-50,2:self.imglines-20])
            exthdu.header["AVERAGE"] = avchan
            hdulist.append(exthdu)

        return hdulist

    def get_extension_header(self, CCDchan, fitshdu, borders = True):
        """
        Builds FITS extension header with position information for each channel.

        :param REBchannel: int
        :return:
        """
        extheader = fitshdu.header
        extheader["NAXIS1"] = self.imgcols
        extheader["NAXIS2"] = self.imglines

        if borders == False:
            parstringlow = '1:2002'
            parstringhigh = '4004:2003'
            colwidth = 512
            extheader['DETSIZE'] = '[1:4096,1:4004]'
            extheader['DATASEC'] = '[11:522,1:2002]'
        else :
            parstringlow = '1:%d' % self.imglines
            parstringhigh = '%d:%d' % (2*self.imglines, self.imglines+1)
            colwidth = self.imgcols
            extheader['DETSIZE'] = '[1:%d,1:%d]' % (self.imgcols*self.nchannels/2, 2*self.imglines)
            extheader['DATASEC'] = '[1:%d,1:%d]' % (self.imgcols, self.imglines)

        if CCDchan < 8:
            pdet = parstringlow
            si = colwidth*(CCDchan+1)
            sf = colwidth*CCDchan+1
        else :
            pdet = parstringhigh
            si = colwidth*(CCDchan-8)+1
            sf = colwidth*(CCDchan-8+1)

        extheader['DETSEC'] = '[%d:%d,%s]' % (si,sf,pdet)

    def make_fits_name(self, imgstr):
        fitsdir = os.path.join(self.fitstopdir,time.strftime('%Y%m%d',time.gmtime()))
        if not os.path.isdir(fitsdir):
            os.mkdir(fitsdir)
        fitsname = os.path.join(fitsdir, imgstr +'.fits')
        return fitsname
    # ===================================================================
    #  Meta data / state of the instrument
    # ===================================================================



# needed elsewhere

#def mock_acquire():
    # stuff to put elsewhere for a full acquisition with header
    #primeheader = {}
    #primeheader["TESTTYPE"] = "Test" DARK:FLAT:OBS:PPUMP:QE:SFLAT
    #DATE
    #TEMP_SET	-95.00
#CCDTEMP	-95.12
#MONDIODE	143.12
#MONOWL	550.00
#FILTER	‘550LP’
#FILENAME	[Original name of the file]
#exthdu = get_sequencer_hdu(self.reb.fpga)