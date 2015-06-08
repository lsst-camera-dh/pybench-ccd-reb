# ! /usr/bin/env python
#
# LSST / LPNHE
#
# Testing REB2

__author__ = 'juramy'

import time
import os
#import subprocess
import lsst.camera.reb.fpga as fpga
import lsst.camera.reb.xml as rebxml
import numpy as np
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

    slicenum = np.ndarray(shape=(prognum,), dtype=np.dtype('a4'))
    output = np.ndarray(shape=(prognum,), dtype=np.dtype('a32'))
    duration = np.ndarray(shape=(prognum,), dtype=np.dtype('i8'))

    for ifunc in range(16):
        func = seq.get_function(ifunc)
        for islice in range(16):
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

class TestREB(object):
    xmlfile = "camera/reb/sequencer-soi.xml"
    rawimgdir = "/home/lsst/test_images"
    fitstopdir = "/home/lsst/test_frames"
    imglines = 2020
    imgcols = 550
    imgtag = 0
    stripes = [0, 1, 2]
    nchannels = 48
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
    min_exposure = int(0.1 / exposure_unit)  # minimal shutter opening time (not used for darks)

    def __init__(self, rriaddress = 2):
        self.f = fpga.FPGA(ctrl_host = None, reb_id = rriaddress)
        #self.load_sequencer()
        self.imgtag = generate_tag(0)
        self.f.set_time(self.imgtag)
        self.full18bits = False  # TODO: check if version of the firmware is 16-bit or 18-bit
        self.config = {}

    def set_stripes(self, liststripes):
        self.stripes = []
        bitval = 0
        for s in liststripes:
            if self.f.check_location(s):
                self.stripes.append(s)
                bitval += 1 << s
        self.f.write(0x400007, bitval)

        if self.stripes == []:
            print("Warning: no stripe selected.")
        if self.full18bits == True and len(self.stripes) > 2 :
            print("Warning: attempting to read 18-bit data for 3 stripes, full image will not fit")
            self.imglines = 1000

        self.nchannels = 16*len(self.stripes)

    def load_sequencer(self):
        """
        Loads all sequencer content.
        :return:
        """
        self.seq = rebxml.fromxmlfile(self.xmlfile)  # use self.seq.program to track addresses
        self.f.send_sequencer(self.seq)
        self.exptime = self.get_exposure_time()

    def select_subroutine(self, subname, repeat = 1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.seq.program == None:
            raise ValueError("No program with identified subroutines yet.")

        if not(self.seq.program.subroutines.has_key(subname)):
            raise ValueError("No subroutine '%s' in the FPGA program." % subname)

        first_instr = fpga.Instruction(
            opcode = fpga.Instruction.OP_JumpToSubroutine,
            address = self.seq.program.subroutines[subname],
            repeat = repeat)

        # print first_instr
        # print first_instr.bytecode()

        # load it at the very beginning of the program (rel addr 0x0)
        self.f.send_program_instruction(0x0, first_instr)
        self.seq.program.instructions[0x0] = first_instr # to keep it in sync

    def update_filetag(self, t):
        self.imgtag = generate_tag(t)
        self.f.set_time(self.imgtag)

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionary and writes to CABAC, then checks the readback.
        Notes: if params is empty, this simply rewrites the same parameters in the CABAC objects and updates config.
        """
        for s in self.stripes:
            for param in iter(params):
                self.f.set_cabac_value(param, params[param], s)

            self.f.send_cabac_config(s)

            time.sleep(0.1)

            self.config.update(self.f.get_cabac_config(s))

            for param in iter(params):
                self.f.check_cabac_value(param, params[param], s)

    def send_aspic_config(self, params):
        """
        Sets ASPIC parameters, writes to ASPIC, then check readback.
        Notes: if params is empty, this simply rewrites the same parameters in the ASPIC objects and updates config.
        """
        for s in self.stripes:
            for param in iter(params):
                self.f.set_aspic_value(param, params[param], s)

            self.f.send_aspic_config(s)

            time.sleep(0.1)

            self.config.update(self.f.get_aspic_config(s, check=True))

    def config_cabac(self):
        """
        Sequence to power up the CCD safely.
        """

        #sets the default sequencer clock states to 0
        self.f.send_function(0, fpga.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0} ))

        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.send_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG": 3.5}
        self.send_cabac_config(og)

        #time.sleep(1)

        #sets clock rails
        dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
        self.f.set_clock_voltages(dacs)
        self.config.update(dacs)

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.send_cabac_config(iclock)
        #time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS": 0xfff}
        for s in self.stripes:
            self.f.set_current_source(dacOS, s)
        self.config.update(dacOS)

        #rewrite default state of sequencer (to avoid reloading all functions)
        self.f.send_function(0, self.seq.get_function(0))


    def config_aspic(self):
        settings = {"GAIN": 0b1000, "RC": 0b11, "AF1": False, "TM": False, "CLS": 0}
        self.send_aspic_config(settings)

    def set_parameter(self, param, value, stripe = 0, location = 3):
        """
        Generic interface to set any single parameter of the REB, and check the readback if possible.
        :param param:
        :param value:
        :return:
        """
        if param in self.f.aspic_top[0].params:
            self.f.set_aspic_value(param, value, stripe, location)
            self.f.send_aspic_config(stripe)
            time.sleep(0.1)
            self.f.get_aspic_config(stripe, check=True)

        elif param in self.f.cabac_top[0].params:
            self.f.set_cabac_value(param, value, stripe)
            self.f.send_cabac_config(stripe)
            time.sleep(0.1)
            self.f.get_cabac_config(stripe)
            self.f.check_cabac_value(param, value, stripe)

        elif param in ["V_SL", "V_SH", "V_RGL", "V_RGH", "V_PL", "V_PH"]:
            self.f.set_clock_voltages({param: value})

        elif param == "I_OS":
            self.f.set_current_source({param: value}, stripe)

        else:
            print("Warning: unidentified parameter for the REB: %s" % param)

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

        return float(iter)*self.exposure_unit  # in seconds

    def set_exposure_time(self, exptime, lighttime=True, darktime=True):
        """
        Modifies exposure subroutines to last the given exposure time
        (input in seconds). By default both exposures with shutter open
        and closed are modified, use optional parameters to preserve one
        or the other.
        :param exptime:
        :param lighttime:
        :param darktime:
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        if lighttime:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            newinstruction = self.seq.program.instructions[exposureadd]
            newinstruction.repeat = int(max(newiter, self.min_exposure))  # This does rewrite the seq.program too
            self.f.send_program_instruction(exposureadd, newinstruction)
        #same for dark subroutine
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            newinstruction = self.seq.program.instructions[darkadd]
            newinstruction.repeat = int(max(newiter, 1))  # must not be 0 or sequencer gets stuck
            self.f.send_program_instruction(darkadd, newinstruction)

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.f.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def execute_sequence(self, name, exposuretime = None):
        """
        Executes a named sequence.
        :param name:
        :param exposuretime:
        :return:
        """
                # load new exposure time here (better: with XML parameter ?)
        if exposuretime:
            self.set_exposure_time(exposuretime)
            self.exptime = exposuretime
        else:
            # else use preset exposure time
            darktime = (name == "Dark")
            self.exptime = self.get_exposure_time(darktime)

        if name == "Bias":
            self.delay = 0
        else:
            self.delay = 100

        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # acquisition date

        # selects the right subroutine as main
        self.select_subroutine(name)
        # starts the sequencer
        self.f.start()
        #freeze until image output (do not send commands while the COB is acquiring)
        time.sleep(self.exptime+3)

    def make_img_name(self):
        return os.path.join(self.rawimgdir,'0x%016x.img' % self.f.get_time())

    def make_fits_name(self, imgstr):
        fitsdir = os.path.join(self.fitstopdir,time.strftime('%Y%m%d',time.gmtime()))
        if not os.path.isdir(fitsdir):
            os.mkdir(fitsdir)
        fitsname = os.path.join(fitsdir, imgstr +'.fits')
        return fitsname

    def conv_to_fits(self, imgname, channels=None):
        """
        Turns img file from imageClient into FITS object.
        """

        # Reading raw file to array
        dt = np.dtype('i4')
        buff = np.fromfile(imgname, dtype=dt)
        # Readies to save next file (could be moved to acquisition function)
        self.update_filetag(self.imgtag + 1)

        # for 18-bit data:
        # negative numbers are translated, sign is inverted on all data, also make all values positive
        # 0 -> 1FFFF, 1FFFF -> 0, 20000 -> 3FFFF, 3FFFF -> 20000
        buffer = np.vectorize(lambda i: 0x5FFFF-i if i & (1 << 17) else 0x1FFFF-i)(buff)
        # TODO: check structure of 16-bit data. It might be already translated back to 18 bits.
        # reshape by channel (all stripes included)
        length = self.imglines * self.imgcols
        buffer = buffer.reshape(length, self.nchannels)

        # Creating FITS HDUs:
        # Create empty primary HDU and fills header
        primaryhdu = pyfits.PrimaryHDU()
        # Create HDU list
        hdulist = pyfits.HDUList([primaryhdu])

        # Add extension for channels HDUs
        for num in range(self.nchannels):
            if channels:  # to skip non-useful channels
                if num not in channels:
                    continue
            chan = buffer[0:length,num]
            chan = chan.reshape(self.imglines, self.imgcols)
            y = chan.astype(np.int32)
            # create extension to fits file for each channel
            exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
            # exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
            self.get_extension_header(num, exthdu)
            avchan = np.mean(y[11:522,1:2002])
            exthdu.header["AVERAGE"] = avchan
            hdulist.append(exthdu)

        # Extended header HDU for REB operating conditions (no readback here, get it from the config dictionary).
        exthdu = pyfits.ImageHDU(name="CCD_COND")
        for keyword in self.config:
            exthdu.header[keyword] = self.config[keyword]
        hdulist.append(exthdu)

        # Sequencer content (no actual readback, get it from the seq object)
        exthdu = get_sequencer_hdu(self.seq)
        hdulist.append(exthdu)

        return hdulist

    def get_extension_header(self, REBchannel, fitshdu, borders = True):
        """
        Builds FITS extension header with position information for each channel.
        New: up to 48 channels for 3 stripes.
        :param REBchannel: int
        :return:
        """
        extheader = fitshdu.header
        extheader["NAXIS1"] = self.imgcols
        extheader["NAXIS2"] = self.imglines
        nstripes = len(self.stripes)

        if borders == False:
            parstringlow = '1:2002'
            parstringhigh = '4004:2003'
            colwidth = 512
            extheader['DETSIZE'] = '[1:%d,1:4004]' % 4096*nstripes
            extheader['DATASEC'] = '[11:522,1:2002]'
        else :
            parstringlow = '1:%d' % self.imglines
            parstringhigh = '%d:%d' % (2*self.imglines, self.imglines+1)
            colwidth = self.imgcols
            extheader['DETSIZE'] = '[1:%d,1:%d]' % (self.imgcols*self.nchannels/2, 2*self.imglines)
            extheader['DATASEC'] = '[1:%d,1:%d]' % (self.imgcols, self.imglines)

        stripe =  REBchannel/16
        CCDchan = REBchannel - stripe * 16 # channel num in CCD
        if CCDchan < 8:
            pdet = parstringlow
            si = colwidth*(CCDchan+stripe*8+1)
            sf = colwidth*(CCDchan+stripe*8)+1
        else :
            pdet = parstringhigh
            si = colwidth*(CCDchan-8+stripe*8)+1
            sf = colwidth*(CCDchan-8+stripe*8+1)

        extheader['DETSEC'] = '[%d:%d,%s]' % (si,sf,pdet)

    def get_meta(self):
        """
        Returns meta data describing the current state
        of the instrument.
        Useful to fill the FITS headers.
        """
        # keys : specify the key order
        keys = ["CTRLCFG", "EXPTIME", "DATE-OBS", "SHUT_DEL", "WIDTH", "HEIGHT", "DETSIZE"]

        # comments : meaning of the keys
        comments = {
            "CTRLCFG" : 'Sequencer XML file',
            "EXPTIME" : 'Exposure time',
            "DATE-OBS": 'Start of frame',
            "SHUT_DEL": 'Shutter close delay in ms',
            "WIDTH"   : 'CCD image width',
            "HEIGHT"  : 'CCD image height',
            "DETSIZE" : 'Detector size',
            }
        # TODO: check official descriptions

        values = {
            "CTRLCFG" : self.xmlfile,
            "EXPTIME" : self.exptime,
            "DATE-OBS": self.timestamp,
            "SHUT_DEL": self.delay,
            "WIDTH"   : self.imgcols,
            "HEIGHT"  : self.imglines,
            "DETSIZE" : '[1:%d,1:%d]' % (self.imgcols*self.nchannels/2, 2*self.imglines),
            }

        return keys, values, comments


def save_to_fits(R, channels=None, fitsname = ""):  # not meant to be part of REB class, will call other instruments
    """
    Managing FITS creation from img file and adding other header information.
    :param R: TestREB
    :param channels: list of channels
    :param fitsname: name if not using default structure.
    :return:
    """
    imgname = R.make_img_name()
    if os.path.isfile(imgname):
        hdulist = R.conv_to_fits(imgname, channels)
        primaryhdu = hdulist[0]
        imgstr = os.path.splitext(os.path.basename(imgname))[0]
        primaryhdu.header["IMAGETAG"] = imgstr
        if not fitsname:
            fitsname = R.make_fits_name(imgstr)
        # else: using LSST scheme for directory and image name, already built in fitsname
        primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
        primaryhdu.header["DATE"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # FITS file creation date
        primaryhdu.header["TESTTYPE"] = 'REB test'
        primaryhdu.header["IMGTYPE"] = 'Bias'  # TODO: update with actual test running
        # TODO: add keyword comments
        # information from REB itself
        primaryhdu.header.update(R.get_meta())
        # also need info from 'localheader.txt'
        localheader = pyfits.Header.fromtextfile("camera/localheader.txt")
        primaryhdu.header.update(localheader)
        # add other instruments here
        #exthdu = pyfits.ImageHDU(name="TEST_COND")
        #... append keys to extension header
        #hdulist.append(exthdu)

        hdulist.writeto(fitsname, clobber=True)
        print("Wrote FITS file "+fitsname)
    else:
        print("Did not find the expected raw file: %s " % imgname)

if __name__ == "__main__":

    R = TestREB()
    R.set_stripes([0, 1, 2])
    R.config_cabac()
    R.config_aspic()
    R.load_sequencer()