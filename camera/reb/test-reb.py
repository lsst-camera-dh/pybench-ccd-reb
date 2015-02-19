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


class TestREB(object):
    xmlfile = "camera/reb/sequencer-soi.xml"
    seq = rebxml.fromxmlfile(xmlfile)  # use self.seq.program to track addresses
    rawimgdir = "/home/lsst/test_images"
    fitstopdir = "/home/lsst/test_frames"
    imglines = 2020
    imgcols = 550
    imgtag = 0
    stripes = [0, 1, 2]

    primeheader = {}
    primeheader["CTRLCFG"] = xmlfile

    def __init__(self):
        self.f = fpga.FPGA()
        self.load_sequencer_fromfile()
        self.imgtag = generate_tag(0)
        self.f.set_time(self.imgtag)

    def load_sequencer_fromfile(self):
        """
        Loads all sequencer content.
        :return:
        """
        self.f.send_sequencer(self.seq)

    def update_filetag(self, t):
        self.imgtag = generate_tag(t)
        self.f.set_time(self.imgtag)

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionary and writes to CABAC, then checks the readback.
        """
        for s in self.stripes:
            for param in iter(params):
                self.f.set_cabac_value(param, params[param], s)

            self.f.send_cabac_config(s)

            time.sleep(0.1)

            self.f.get_cabac_config(s)

            for param in iter(params):
                self.f.check_cabac_value(param, params[param], s)

    def send_aspic_config(self, params):
        """
        Sets ASPIC parameters, writes to ASPIC, then check readback.
        """
        for s in self.stripes:
            for param in iter(params):
                self.f.set_aspic_value(param, params[param], s)

            self.f.send_aspic_config(s)

            time.sleep(0.1)

            self.f.get_aspic_config(s, check=True)


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

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.send_cabac_config(iclock)

        #time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS": 0xfff}
        for s in self.stripes:
            self.f.set_current_source(dacOS, s)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.f.send_function(0, fpga.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0x6bc, 1: 0}))


    def config_aspic(self):
        settings = {"GAIN": 0b1000, "RC": 0b11, "AF1": False, "TM": False, "CLS": 0}
        self.send_aspic_config(settings)

if __name__ == "__main__":

