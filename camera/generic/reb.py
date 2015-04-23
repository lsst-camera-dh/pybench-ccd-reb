#
# LSST / LPNHE
# Author: Claire Juramy, Laurent Le Guillou
#
"""
Generic REB object. The specific details for each board should be
added in their specific object.
REB talks to the generic FPGA object. This should be overwritten
in children REB objects to talk to the appropriate FPGA.
"""
import time
import os
import string
import numpy as N
import pyfits
import fpga

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
    full18bits = True # TODO: check from version of the firmware
    # to be loaded from XML later
    imglines = 2020
    imgcols = 550
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
    min_exposure = int(0.1 / exposure_unit)  # minimal shutter opening time (not used for darks)

    # ===================================================================

    def __init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0]):
        self.fpga = fpga.FPGA(ctrl_host, reb_id)
        self.set_stripes(stripe_id)  # stripe in use
        self.recover_filetag()  # in case we are recovering from software reboot and not hardware reboot
        self.seq = None  # will be filled when loading the sequencer

    def set_stripes(self, liststripes):
        self.stripes = []
        bitval = 0
        for s in liststripes:
            if fpga.check_location(s):
                self.stripes.append(s)
                bitval += 1 << s
        self.fpga.write(0x400007, bitval)

        if self.stripes == []:
            print("Warning: no stripe selected.")
        if self.full18bits == True and len(self.stripes) > 2 :
            print("Warning: attempting to read 18-bit data for 3 stripes, full image will not fit")
            self.imglines = 1000

        self.nchannels = 16*len(self.stripes)

   # --------------------------------------------------------------------
    def update_filetag(self, t):
        """
        Updates the filetag to the FPGA timer.
        :param t: int new numerical tag
        :return:
        """
        hextag = generate_tag(t)
        self.imgtag = t
        self.fpga.set_time(hextag)

    def recover_filetag(self):
        """
        Reads the filetag from the FPGA timer and recovers imgtag if it is in the right format.
        Returns the tag.
        :return: string
        """
        t = self.fpga.get_time()
        tagstr = '0x%016x' % t
        todaystr = time.strftime('%Y%m%d', time.gmtime())
        if string.find(tagstr, todaystr) > -1:
            self.imgtag = int(tagstr[-5:], base=10)

        return tagstr


   # --------------------------------------------------------------------
    def load_sequencer(self, xmlfile=None):
        """
        Loads all sequencer content.
        :return:
        """
        if xmlfile:
            self.xmlfile = xmlfile

        self.seq = rebxml.fromxmlfile(self.xmlfile)  # use self.seq.program to track addresses
        self.fpga.send_sequencer(self.seq)
        try:
            self.exptime = self.get_exposure_time()
        except:
            print("Warning: could not find exposure subroutine in %s" % xmlfile)
        self.name = ""  # there is actually no way to access that from self.seq

    def select_subroutine(self, subname, repeat=1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.seq.program == None:
            raise ValueError("No program with identified subroutines yet.")

        if not (self.seq.program.subroutines.has_key(subname)):
            raise ValueError("No subroutine '%s' in the FPGA program." % subname)

        first_instr = fpga.Instruction(
            opcode="JSR",
            address=self.seq.program.subroutines[subname],
            repeat=repeat)

        # load it at the very beginning of the program (rel addr 0x0)
        self.fpga.send_program_instruction(0x0, first_instr)
        self.seq.program.instructions[0x0] = first_instr  # to keep it in sync
        self.name = subname

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

    def set_exposure_time(self, exptime):
        """
        Modifies exposure subroutines to last the given exposure time
        (input in seconds).
        :param exptime: float
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        exposureadd = self.seq.program.subroutines[self.exposuresub]
        newinstruction = self.seq.program.instructions[exposureadd]
        newinstruction.repeat = int(max(newiter, self.min_exposure))  # This does rewrite the seq.program too
        self.fpga.send_program_instruction(exposureadd, newinstruction)

    def set_dark_time(self, exptime):
        """
        Modifies 'dark' exposure (shutter closed) subroutines to last the given exposure time
        (input in seconds).
        :param exptime:
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        darkadd = self.seq.program.subroutines[self.darksub]
        newinstruction = self.seq.program.instructions[darkadd]
        newinstruction.repeat = int(max(newiter, 1))  # must not be 0 or sequencer gets stuck
        self.fpga.send_program_instruction(darkadd, newinstruction)
    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.fpga.get_input_voltages_currents()

     # --------------------------------------------------------------------

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.fpga.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def config_sequence(self, name, exptime, shutdelay=100):
        """
        Configure the programmed sequence. Used also to record parameters.
        """
        self.wait_end_sequencer()
        self.select_subroutine(name)

        if name in ["Bias", "Test", "Wait"]:
            self.shutdelay = 0
            self.exptime = 0
        else:
            self.shutdelay = shutdelay
            self.exptime = exptime
            if name == "Dark":
                self.set_dark_time(exptime)
            else:
                self.set_exposure_time(exptime)

    def execute_sequence(self):
        """
        Executes the currently loaded sequence.
        """
        self.wait_end_sequencer()
        self.tstamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.fpga.start()
        print("Starting %s sequence with %f exposure time." % (self.name, self.exptime))
        #freeze until image output (do not send commands while the COB is acquiring)
        time.sleep(self.exptime+3)

    def waiting_sequence(self, name="Wait"):
        """
        Lets CCD wait by clearing periodically until keyboard interrupt is sent.

        """
        self.config_sequence(name, 0)
        keepwaiting = True
        while keepwaiting:
            try:
                self.execute_sequence()
                time.sleep(60)
            except KeyboardInterrupt:
                keepwaiting = False

    # --------------------------------------------------------------------
    def make_img_name(self):
        return os.path.join(self.rawimgdir,'0x%016x.img' % self.f.get_time())
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