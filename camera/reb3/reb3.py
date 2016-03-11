#! /usr/bin/env python
#
# LSST / LPNHE
#
# Testing REB3
#
# Usage:
# import lsst.camera.reb3.reb3 as reb3

__author__ = 'juramy'

import lsst.camera.generic.reb as reb
import time
import os
import logging
import fpga
import astropy.io.fits as pyfits


class REB3(reb.REB):

    xmldir = "/home/lsst/lsst/py/camera/reb3/"

    def __init__(self, rriaddress = 2, ctrl_host = None, stripe_id=[0], hardware='REB3'):
        reb.REB.__init__(self, rriaddress, ctrl_host, stripe_id)
        self.fpga = fpga.FPGA3(ctrl_host, rriaddress, hardware)
        self.xmlfile = "sequencer-reb3.xml"
        self.exposure_unit = 0.025  # duration of the elementary exposure subroutine in s
        self.min_exposure = int(0.1 / self.exposure_unit)  # minimal shutter opening time (not used for darks)

     # --------------------------------------------------------------------

    def send_aspic_config(self, params):
        """
        Sets ASPIC parameters, writes to ASPIC, then checks readback.
        Notes: if params is empty, this simply rewrites the same parameters in the ASPIC objects and updates config.
        """
        for s in self.stripes:
            for param in iter(params):
                self.fpga.set_aspic_value(param, params[param], s)
            self.fpga.get_aspic_config(s, check=True)

    def get_aspic_config(self):
        """
        Reads ASPIC configurations from the SPI readback.
        :return:
        """
        config = self.fpga.get_aspic_config(self.stripes[0])
        if len(self.stripes) > 1:
            for stripe in self.stripes[1:]:
                config.update(self.fpga.get_aspic_config(stripe))

        return config

    def config_aspic(self):
        settings = {"GAIN": 0b1, "RC": 0b101, "AF1": False, "TM": False, "CLS": 0}
        self.send_aspic_config(settings)

    def set_biases(self, params):
        """
        Manages safe changes in bias values from CABAC, or sets alternative biases.
        :param params: dict
        :return:
        """
        # simultaneous activation works fine if all new values are valid (not checked here)
        for s in self.stripes:
            self.fpga.set_bias_voltages(params, s)

    def get_biases(self):
        """
        Reads configuration of biases (replaces CABAC readback).
        :return:
        """
        config = self.fpga.get_bias_voltages(self.stripes[0], readback=True)
        if len(self.stripes) > 1:
            for s in self.stripes[1:]:
                config.update(self.fpga.get_bias_voltages(s), readback=True)
        return config

    def set_parameter(self, param, value, stripe = 0, location = 3):
        """
        Generic interface to set any single parameter of the REB, and check the readback if possible.
        :type param: basestring
        :param stripe:
        :param location:
        :param param:
        :param value:
        :return:
        """
        if param in ["GAIN", "RC", "AF1", "TM", "CLS"]:
            self.fpga.set_aspic_value(param, value, stripe, location)
            time.sleep(0.1)
            self.fpga.get_aspic_config(stripe, check=True)

        elif param in self.fpga.groups['CLOCKS']:
            self.fpga.set_clock_voltages({param: value})

        elif param in self.fpga.groups['BIASES']:
            self.fpga.set_bias_voltages({param: value}, stripe)

        elif param == "CS":
            self.fpga.set_current_source(value, stripe)

        else:
            print("Warning: unidentified parameter for the REB: %s" % param)

    # --------------------------------------------------------------------

    def REBpowerup(self):
        """
        To be executed at power-up.
        :return:
        """
        self.fpga.write(0x400006, 0)  # pattern generator off
        # stops the clocks to use as image tag
        self.fpga.stop_clock()

        #load sequencer (from compiled self.seq or from self.xmlfile if not compiled)
        self.load_sequencer()
        # load 0 on default state to prep for CCD start-up
        self.fpga.send_function(0, fpga.Function(name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

        # configure ASPIC with default values
        self.config_aspic()


    def CCDpowerup(self):
        """
        Sequence to power up the CCD.
        """

        # starting drain voltages

        self.set_biases({'OD': 29, 'RD': 18, 'GD': 24})

        time.sleep(0.5)

        #starting OG voltage
        og = {"OG": 3.}
        self.set_biases(og)

        time.sleep(0.5)

        #settings clock rails
        rails = {"SL": 0.5, "SU": 9.5, "RGL": 0, "RGU": 12, "PL": 0, "PU": 9.0}
        self.fpga.set_clock_voltages(rails)

        #puts current on CS gate
        dacOS = 0xfff
        for s in self.stripes:
            self.fpga.set_current_source(dacOS, s)

        #load sequencer if not done, else rewrite default state of sequencer (to avoid reloading all functions)
        if self.seq:
            self.fpga.send_function(0, self.seq.get_function(0))
        else:
            self.load_sequencer(self.xmlfile)

        self.fpga.enable_bss(True)
        print('BSS can be powered on now.')

    def CCDshutdown(self):
        """
        Sequence to shutdown power to the CCD.
        """
        print('BSS should be shutdown at this time.')
        time.sleep(5)
        # This works, but it is common to all stripes  
        self.fpga.enable_bss(False)

        # clock rails first (in V)
        rails = {"SL": 0, "SU": 0, "RGL": 0, "RGU": 0, "PL": 0, "PU": 0}
        self.fpga.set_clock_voltages(rails)

        #sets the default sequencer clock states to 0
        self.fpga.send_function(0, fpga.Function(name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

        #shuts current on CS gate
        dacOS = 0
        for s in self.stripes:
            self.fpga.set_current_source(dacOS, s)


        time.sleep(0.1)

        # shuts OG voltage
        og = {"OG": 0}
        self.set_biases(og)

        time.sleep(0.5)

        #shutting drain voltages
        self.set_biases({'OD': 0, 'RD': 0, 'GD': 0})

        time.sleep(0.5)
        print('CCD shutdown complete on REB3.')

    def REBshutdown(self):
        """
        Old: to be executed when shutting down the REB3.
        :return:
        """
        pass

    # --------------------------------------------------------------------

    def increment(self, offset=0):
        """
        Increments the ADC sampling signal by 1 FPGA clock cycle (10 ns) every sampling, up to 255.
        :type offset: int
        :param offset: offset at the first sample
        """
        self.fpga.increment(offset)
        self.window_sequence(True)

    def stop_increment(self):
        """
        Returns to normal configuration after increment().
        """
        self.fpga.stop_increment()
        self.window_sequence(False)

 # --------------------------------------------------------------------


def save_to_fits(R, channels=None, rawimg='', fitsname = ""):  # not meant to be part of REB class, will call other instruments
    """
    Managing FITS creation from img file and adding other header information.
    :type R: lsst.camera.reb3.reb3.REB3
    :param channels: list of channels
    :param fitsname: name if not using default structure.
    :return:
    """
    if rawimg:
        imgname = rawimg
    else:
        imgname = R.make_img_name()
    if os.path.isfile(imgname):
        hdulist = reb.conv_to_fits(imgname, R.imgcols, R.imglines, R.nchannels, channels, displayborders=True)
        primaryhdu = hdulist[0]
        imgstr = os.path.splitext(os.path.basename(imgname))[0]
        primaryhdu.header["IMAGETAG"] = imgstr
        if not fitsname:
            fitsname = reb.make_fits_name(R.fitstopdir, imgstr)
        # else: using LSST scheme for directory and image name, already built in fitsname
        primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
        primaryhdu.header["DATE-OBS"] = R.tstamp
        primaryhdu.header["TESTTYPE"] = 'REB3 test'
        primaryhdu.header["IMGTYPE"] = R.seqname
        localheader = pyfits.Header.fromtextfile("localheader.txt")
        primaryhdu.header.update(localheader)
        # for more meta, use the driver ccd_reb.py
        # from FPGA object:
        #exthdu = pyfits.ImageHDU(name="CCD_COND")

        #headerdict.update(R.get_cabac_config())
        #headerdict.update(R.get_aspic_config())
        #for keyword in headerdict:
        #    exthdu.header[keyword] = headerdict[keyword]
        #hdulist.append(exthdu)
        #headermeta = R.get_meta_operating()
        #for key in headermeta.keys:
        #    exthdu.header[key] = (headermeta.values[key], headermeta.comments[key])
        # Sequencer content (no actual readback, get it from the seq object)
        seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=reb.get_sequencer_string(R.seq),
                                                         ascii=True)])
        seqhdu.header['EXTNAME'] = 'SEQUENCER'
        hdulist.append(seqhdu)

        hdulist.writeto(fitsname, clobber=True)

        print("Wrote FITS file "+fitsname)
    else:
        print("Did not find the expected raw file: %s " % imgname)

if __name__ == "__main__":

    logfile = os.path.join('/home/lsst/logs', time.strftime('wreb-log-%Y%m%d.txt', time.gmtime()))
    logging.basicConfig(filename = logfile,
                        level = logging.DEBUG,
                        format = '%(asctime)s: %(message)s')
    #r = reb3.REB3(rriaddress=0x2, stripe_id=[1])
    r = REB3(rriaddress=0x2, stripe_id=[1])
    # here power on power supplies
    r.REBpowerup()
    time.sleep(0.1)
    r.CCDpowerup()
    r.config_aspic()
    #r.load_sequencer('sequencer-scan.xml')
    #r.select_subroutine("Bias")
    #r.execute_sequence()
    #reb3.save_to_fits(r)

    #r.increment()
    #r.execute_sequence()
    #reb3.save_to_fits(r)
    #r.stop_increment()
    
    #recovery from FPGA power down (no CCD)
    #r.set_stripes([0,1,2])
    #r.read_sequencer_file('sequencer-scan.xml')
    #r.select_subroutine("Bias")
    #r.config_aspic()
    
    
