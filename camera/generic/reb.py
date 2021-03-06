#
# LSST / LPNHE
# Author: Claire Juramy, Laurent Le Guillou
#
"""
Generic REB object. The specific operations for each board should be added in their specific object
inheriting from this one.
Generic REB talks to the generic FPGA object. This should be overwritten in inheritor REB objects to
talk to the appropriate FPGAs (which will inherit from the generic FPGA object).
"""

import time
import datetime
import os
import numpy as N
import astropy.io.fits as pyfits
import fpga
import rebxml


def generate_tagstr():
    tagstr = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    return tagstr

def generate_hextag(tagstr):
    hextag = int(tagstr, 16)
    return hextag

def utc_now_isoformat():
    return datetime.datetime.utcnow().isoformat()

# Sequencer representation

def get_sequencer_hdu(seq):
    """
    Builds table HDU for FITS file containing sequencer dump
    :param seq: Sequencer
    :return: pyfits.TableHDU
    """
    prog = seq.program
    progaddr = prog.instructions.keys()
    prognum = 256 + len(progaddr)

    slicenum = N.zeros(shape=(prognum,), dtype=N.dtype('a4'))
    output = N.zeros(shape=(prognum,), dtype=N.dtype('a32'))
    duration = N.zeros(shape=(prognum,), dtype=N.dtype('i8'))

    for ifunc in seq.functions:
        func = seq.get_function(ifunc)
        for islice in func.outputs.keys():
            i = ifunc * 16 + islice
            slicenum[i] = hex(i)[2:]
            output[i] = bin(func.outputs[islice])[2:]
            duration[i] = func.timelengths[islice]

    for i, addr in enumerate(sorted(progaddr)):
        slicenum[i+256] = '3' + '%03x' % addr
        output[i+256] = prog.instructions[addr].__repr__()[:20]
        duration[i+256] = prog.instructions[addr].repeat

    slicecol = pyfits.Column(name="Address", format='A4', array=slicenum)
    outputcol = pyfits.Column(name="Output", format='A32', array=output)
    durationcol = pyfits.Column(name="Time", format='I8', array=duration)

    exthdu = pyfits.new_table([slicecol, outputcol, durationcol], tbtype='TableHDU')
    # add name to extension here
    exthdu.header["EXTNAME"] = "SEQ_CFG"

    return exthdu


def get_sequencer_string(seq):
    """
    Builds a string table representation of the sequencer content in seq.
    :ptype seq: Sequencer
    :return: N.array
    """
    reprarray = N.zeros(shape=(0,), dtype=N.dtype('a73'))

    # all functions
    for ifunc in seq.functions:
        reprfunc = seq.functions[ifunc].__repr__()
        for l in reprfunc.splitlines():
            if l:
                reprarray = N.append(reprarray, l.expandtabs(8))

    # splitting the subroutine stack into array lines
    reprprog = seq.program.__repr__()
    for l in reprprog.splitlines():
        reprarray = N.append(reprarray, l)

    # adding the pointer values if any
    for p in seq.pointers:
        reprarray = N.append(reprarray, seq.pointers[p].__repr__())

    return reprarray

# FITS mosaic formating


def get_detsize(imgcols, imglines, nchannels, channels=None, displayborders=False):
    """
    Builds detector size information for the FITS header.
    If borders is True, includes all read pixels in DETSIZE.
    If only some channels are selected, puts them side by side.
    :return: string
    """
    if channels:
        if displayborders:
            detstring = '[1:%d,1:%d]' % (imgcols * len(channels), imglines)
        else:
            detstring = '[1:%d,1:2002]' % (512 * len(channels))
    else:
        if displayborders:
            detstring = '[1:%d,1:%d]' % (imgcols * nchannels / 2, 2 * imglines)
        else:
            detstring = '[1:%d,1:4004]' % (nchannels * 256)

    return detstring


def get_extension_header(imgcols, imglines, CCDchan, fitshdu, detstring, channels=None, displayborders=False):
    """
    Builds FITS extension header with position information for each channel.
    If displayborders is True, includes all read pixels in DATASEC display.
    :type CCDchan: int
    :type fitshdu: pyfits.HDU
    :type detstring: basestring
    :type channels: list
    :type displayborders: bool
    :return:
    """
    extheader = fitshdu.header
    extheader["NAXIS1"] = imgcols
    extheader["NAXIS2"] = imglines
    extheader['DETSIZE'] = detstring
    extheader['CHANNEL'] = CCDchan

    if displayborders:
        parstringlow = '1:%d' % imglines
        parstringhigh = '%d:%d' % (2 * imglines, imglines + 1)
        colwidth = imgcols
        extheader['DATASEC'] = '[1:%d,1:%d]' % (imgcols, imglines)
    else:
        parstringlow = '1:2002'
        parstringhigh = '4004:2003'
        colwidth = 512
        extheader['DATASEC'] = '[11:522,1:2002]'

    if channels:  # put them in a row
        pdet = parstringlow
        si = colwidth * CCDchan +1
        sf = colwidth * (CCDchan + 1)
    else:
        numCCD = CCDchan / 16
        chan = CCDchan - numCCD * 16
        if chan < 8:
            pdet = parstringlow
            si = colwidth * (CCDchan - 8 * numCCD + 1)
            sf = colwidth * (CCDchan - 8 * numCCD) + 1
        else:
            pdet = parstringhigh
            si = colwidth * (CCDchan - 8 * (numCCD + 1)) + 1
            sf = colwidth * (CCDchan - 8 * (numCCD + 1) + 1)

    extheader['DETSEC'] = '[%d:%d,%s]' % (si, sf, pdet)

    # this is valid in any case with a CCD
    extheader['BIASSEC'] = ('[523:544,1:2002]', 'Serial overscan region')


def make_fits_name(fitstopdir, imgstr, compressed=True):
    """
    Builds a complete FITS file path.
    Takes the root name of imgstr as FITS name.
    :type imgstr: string
    :type compressed: bool
    :return: string
    """
    fitsdir = os.path.join(fitstopdir, time.strftime('%Y%m%d', time.gmtime()))
    if not os.path.isdir(fitsdir):
        os.mkdir(fitsdir)

    rootname = os.path.splitext(os.path.basename(imgstr))[0]

    fitsname = os.path.join(fitsdir, rootname + (compressed and '.fz' or '.fits'))

    return fitsname


def conv_to_fits(imgname, imgcols, imglines, nchannels, channels=None, displayborders=False):
    """
    Creates the fits object from the acquired data.
    If channels is not None, it is the list of channels to be saved.
    :param imgname: file in .img format
    :param imgcols: columns in a single channel
    :param imglines: lines in a single channel
    :param nchannels: total number of channels acquired
    :param channels: selected channels to convert to fits, if not None
    :param displayborders: if the displayed image will include the non-exposed areas
    """

    # Reading raw file to array
    dt = N.dtype('i4')
    buff = N.fromfile(imgname, dtype=dt)

    # for 18-bit data:
    # negative numbers are translated, sign is inverted on all data, also make all values positive
    # 0 -> 1FFFF, 1FFFF -> 0, 20000 -> 3FFFF, 3FFFF -> 20000
    # this works by XORing the lowest 17 bits
    rawdata = N.bitwise_xor(buff, 0x1FFFF)
    # reshape by channel
    length = imglines * imgcols
    rawdata = rawdata.reshape(length, nchannels)

    # Creating FITS HDUs:
    # Create empty primary HDU and fills header
    primaryhdu = pyfits.PrimaryHDU()
    detstring = get_detsize(imgcols, imglines, nchannels, channels, displayborders)
    primaryhdu.header['DETSIZE'] = (detstring, 'NOAO MOSAIC keywords')
    primaryhdu.header['WIDTH'] = (imgcols, 'CCD columns per channel')
    primaryhdu.header['HEIGHT'] = (imglines, 'CCD lines per channel')
    # Create HDU list
    hdulist = pyfits.HDUList([primaryhdu])

    # Add extensions for channels HDUs
    for num in range(nchannels):
        if channels:  # to skip non-useful channels
            if num not in channels:
                continue
        chan = rawdata[0:length, num]
        chan = chan.reshape(imglines, imgcols)
        y = chan.astype(N.int32)
        # create extension to fits file for each channel
        #if self.compression:
        exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
        #else:
            #exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
        get_extension_header(imgcols, imglines, num, exthdu, detstring, channels, displayborders)
        avchan = N.mean(y[11:imgcols-50, 2:imglines-20])
        exthdu.header["AVERAGE"] = avchan
        hdulist.append(exthdu)

    return hdulist

# =======================================================================


class REB(object):
    rawimgdir = "/data/raw/"
    fitstopdir = "/data/frames/"
    xmldir = "/home/lsst/lsst/py/camera/generic/"
    full18bits = True  # TODO: check from version of the firmware
    # compression = True
    # will be reloaded from XML later
    imglines = 2020
    imgcols = 550
    exposuresub = "Exposure"
    darksub = "DarkExposure"

    # ===================================================================

    def __init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0]):
        self.fpga = fpga.FPGA(ctrl_host, reb_id)
        self.stripes = []
        self.nchannels = 0  # total number of channels acquired
        self.set_stripes(stripe_id)  # stripe in use
        #self.imgtag = 0  # this is now a string, filled in update_filetag
        #self.recover_filetag()  # in case we are recovering from software reboot
        self.update_filetag()
        self.xmlfile = "sequencer-soi.xml"
        self.exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
        self.min_exposure = int(0.1 / self.exposure_unit)  # minimal shutter opening time (not used for darks)
        # initialize parameters for frames
        self.seq = None  # will be filled when loading the sequencer
        self.exptime = 0
        self.shutdelay = 0
        self.tstamp = 0
        self.seqname = ""  # there is actually no way to access that from self.seq, filled when called by name
        self.memorized_sequence = 'Bias'  # used when switching to a peculiar sequence

    def set_stripes(self, liststripes):
        self.stripes = []
        bitval = 0
        for s in liststripes:
            if fpga.check_location(s):
                self.stripes.append(s)
                bitval += 1 << s
        self.fpga.write(0x400007, bitval)

        if not self.stripes:
            print("Warning: no stripe selected.")
        if self.full18bits and len(self.stripes) > 2:
            print("Warning: attempting to read 18-bit data for 3 stripes, full image will not fit")

        self.nchannels = 16*len(self.stripes)

   # --------------------------------------------------------------------

    def update_filetag(self):
        """
        Updates the filetag from the current time and writes it to the
        FPGA timer.
        :param t: int
        :return:
        """
        t = generate_tagstr()
        hextag = generate_hextag(t)
        self.imgtag = t
        self.fpga.set_time(hextag)

    # def recover_filetag(self):
    #     """
    #     Reads the filetag from the FPGA timer and recovers imgtag if it is in the right format.
    #     Returns the tag.
    #     :return: string
    #     """
    #     t = self.fpga.get_time()
    #     tagstr = '0x%016x' % t
    #     todaystr = time.strftime('%Y%m%d', time.gmtime())
    #     if string.find(tagstr, todaystr) > -1:
    #         self.imgtag = int(tagstr[-5:], base=10)
    #
    #     return tagstr

   # --------------------------------------------------------------------

    def read_sequencer_file(self, xmlfile):
        """
        Reads sequencer file to internal variable self.seq.
        :return:
        """
        self.xmlfile = xmlfile
        
        self.seq = rebxml.fromxmlfile(os.path.join(self.xmldir, self.xmlfile))

    def load_sequencer(self, xmlfile=None):
        """
        Loads all sequencer content.
        :return:
        """
        if xmlfile:
            self.read_sequencer_file(xmlfile)
        # otherwise use self.seq already loaded
        else:
            if not self.seq:
                self.read_sequencer_file(self.xmlfile)

        self.wait_end_sequencer()
        self.fpga.send_sequencer(self.seq)

        self.imglines = self.seq.parameters['ReadLines']
        self.imgcols = self.seq.parameters['ReadColumns']

        try:
            self.exptime = self.get_exposure_time()
        except:
            print("Warning: could not find exposure subroutine in %s" % xmlfile)

        # select a subroutine to fill self.seqname
        self.select_subroutine('Bias')

    def select_subroutine(self, subname, repeat=1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.seq.program is None:
            raise ValueError("No program with identified subroutines yet.")

        if subname not in self.seq.program.subroutines:
            raise ValueError("No subroutine '%s' in the FPGA program." % subname)

        first_instr = fpga.Instruction(opcode="JSR",
                                       address=self.seq.program.subroutines[subname],
                                       repeat=repeat)

        # load it at the very beginning of the program (rel addr 0x0)
        self.wait_end_sequencer()
        self.fpga.send_program_instruction(0x0, first_instr)
        self.seq.program.instructions[0x0] = first_instr  # to keep it in sync
        self.seqname = subname
        print('Sequencer program set to %s' % subname)

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
        iterexp = instruction.repeat
        self.exptime = float(iterexp) * self.exposure_unit  # in seconds

        return self.exptime

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
        self.wait_end_sequencer()
        self.fpga.send_program_instruction(exposureadd, newinstruction)

        # self.exptime = newiter * self.exposure_unit  # better re-read due to light/dark difference

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
        self.wait_end_sequencer()
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

    def config_sequence(self, name, exptime=0.1, shutdelay=100):
        """
        Configure the programmed sequence. Used also to record parameters.
        """
        # wait_end_sequencer is now included in select_subroutine
        self.select_subroutine(name)

        if name in ["Bias", "Test", "Wait", "ClearBias", 'InfiniteWait']:
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
        if self.seqname not in ['Wait', 'InfiniteWait']:
            self.update_filetag()
        self.tstamp = utc_now_isoformat()
        self.fpga.start()
        print("Starting %s sequence with %f exposure time." % (self.seqname, self.exptime))
        #freeze until image output (do not send commands while the COB is acquiring)
        #time.sleep(self.exptime+3)

    def waiting_sequence(self, name="InfiniteWait", start=True):
        """
        Lets CCD wait by clearing infinitely until stop is sent.
        When stopping, sends the stop command to the infinite loop and replaces it with the named sequence,
        or the memorized sequence if None.
        """
        if start:
            self.memorized_sequence = self.seqname
            self.select_subroutine(name)
            self.execute_sequence()
        else:
            self.fpga.stop()
            if name:
                self.select_subroutine(name)
            else:
                self.select_subroutine(self.memorized_sequence)

    def window_sequence(self, on=True):
        """
        Reduces to a window or goes back to previous full size sequence.
        :param on:
        :return:
        """
        if on:
            self.memorized_sequence = self.seqname
            self.select_subroutine('Window')
            self.imgcols = self.seq.parameters['WindowColumns']
            self.imglines = self.seq.parameters['WindowLines']
        else:
            self.select_subroutine(self.memorized_sequence)
            self.imgcols = self.seq.parameters['ReadColumns']
            self.imglines = self.seq.parameters['ReadLines']

    # --------------------------------------------------------------------

    def make_img_name(self):
        """
        Reconstitutes the path for the latest raw file created (does not necessarily exists).
        :return: string
        """
        return os.path.join(self.rawimgdir, '0x%016x.img' % self.fpga.get_time())

    # --------------------------------------------------------------------

    def get_meta_operating(self):
        """
        Gets all REB operating parameters. For headers and checks.
        :return:
        """

        config = self.fpga.get_fpga_config(self.stripes[0])
        if len(self.stripes) > 1:
            for stripe in self.stripes[1:]:
                config.update(self.fpga.get_fpga_config(stripe))

        return config

