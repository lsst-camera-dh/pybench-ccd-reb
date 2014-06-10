#! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import lsst.camera.reb as reb
import lsst.camera.fpga as fpga
import time
import xmlrpclib


class Bench(object):
    """
    Internal representation of the full bench
    """
    opheader = {}
    testheader = {}
    primeheader = {}
    sequencerheader = {}
    slitsize = 30

    def __init__(self):
        self.reb = reb.REB()
        self.bss = xmlrpclib.ServerProxy("http://lpnlsst.in2p3.fr:8087/")
        self.bss.connect()
        # implementation with remote control
        # other instruments: create object here, does not connect
        self.qth = xmlrpclib.ServerProxy("http://lpnlsst:")
        self.xehg = xmlrpclib.ServerProxy("http://lpnlsst:8089/")
        self.triax = xmlrpclib.ServerProxy("http://lpnlsst:8086/")
        self.laser = xmlrpclib.ServerProxy("http://lpnlsst:")

    def powerup(self):
        """
        Sequence to power up the CCD safely.
        """
        
        #sets the default sequencer clock states to 0
        self.reb.load_function(0, fpga.Function(name = "default state",
                                                timelengths = {0:2, 1:0},
                                                outputs = {0:0, 1:0}))

        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.reb.set_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG":3.5}
        self.reb.set_cabac_config(og)

        time.sleep(1)

        #sets clock rails
        dacs = {"V_SL":0,"V_SH":8.03,"V_RGL":0,"V_RGH":8.03,"V_PL":0,"V_PH":9.13}
        self.reb.set_dacs(dacs)


        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.reb.set_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS":  0xfff}
        self.reb.set_dacs(dacOS)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.reb.load_function(0, fpga.Function(name = "default state",
                                                timelengths = {0:2, 1:0},
                                                outputs = {0:0x6bc, 1:0}))


        time.sleep(1)

        #starts Keithley backsubstrate voltage
        setvolt = 40
        self.config_bss(setvolt)
        self.bss.setVoltageOperate(1)
        while abs(self.bss.getVoltage()-setvolt) > 0.1:
             time.sleep(1)
        print("Start-up sequence complete")


    def shutdown(self):
        """
        Sequence to shut down the CCD safely
        """
        
        #Back-substrate first
        self.bss.setVoltageOperate(0)

        while abs(self.bss.getVoltage()) > 0.1:
             time.sleep(1)

        #current source
        self.reb.set_dacs({"I_OS":0})
        
        time.sleep(1)

        #clock states to 0
        self.reb.load_function(0, fpga.Function(name = "default state",
                                                timelengths = {0:2, 1:0},
                                                outputs = {0:0, 1:0}))
        #currents on CABAC clocks to 0
        self.reb.set_cabac_config({"IC": 0})
        #clock rails to 0
        self.reb.set_dacs({"V_SL":0,"V_SH":0,"V_RGL":0,"V_RGH":0,"V_PL":0,"V_PH":0})
        
        time.sleep(1)

        #currents on OG to 0
        self.reb.set_cabac_config({"OG": 0})

        time.sleep(1)

        #drains to 0
        self.reb.set_cabac_config({"OD": 0, "GD": 0, "RD": 0})

        print("CCD shutdown complete")

    def config_bss(self, voltage = 40):
        """
        Configuration of Keithley 6487 used to generate back-substrate voltage.
        """
        
        if voltage < 50:
            range = 50.0
        else:
            range = 500.0
        self.bss.selectOutputVoltageRange(range, 2.5e-5)
        
        self.bss.setOutputVoltage(voltage)

        self.bss.zeroCorrect()
        self.bss.selectCurrent(2e-5)

    def set_slit_size(self, slitsize):
        """
        Sets both slit sizes on the monochromator and waits until complete
        :param slitsize:
        :return:
        """
        self.slitsize = slitsize
        self.triax.setInSlit(self.slitsize)
            while self.triax.status() == 0:
                time.sleep(1.0)
            self.triax.setOutSlit(self.slitsize)
            while self.triax.status() == 0:
                time.sleep(1.0)


    def move_to_wavelength(self, wavelength, SelectGrating = False):
        """
        Moves the monochromator to the selected wavelength and waits until it is done.
        Calculates automatically which grating to use if authorized to change.
        """
        if SelectGrating:
            if wavelength < 800:
                grating = 0
                lines = 1198
            elif wavelength <1400:
                grating = 1
                lines = 599
            else:
                grating = 2
                lines = 599  # TODO: check values
            self.triax.setGrating(grating)  # TODO: check this is the right method
            self.testheader["MONOPOS"] = grating
            self.testheader["MONOGRAT"] = lines

        self.triax.setWavelength(wavelength)
        while self.triax.status() == 0:
            time.sleep(1.0)



    def select_source(self, sourcetype, wavelength = 500.0):
        """
        Connects and starts whichever light source is going to be used
        """
        if sourcetype == "Fe55":
            pass  # will be motorized at some point
        elif sourcetype == "laser":
            self.laser.connect()
            # TODO: selects output based on wavelength
        elif sourcetype == "qth":
            self.qth.connect()
            # TODO: start lamp here
        elif sourcetype == "xehg":
            self.xehg.connect()
            # TODO: start lamp here
        else:
            raise IOError("Unknown type of source")
        self.testheader["SRCTYPE"] = sourcetype.upper()
        #self.testheader["SCRMODL"]  # source model
        #self.testheader["SRCPWR"]  # source power in Watts

        if sourcetype in ["qth", "xehg"]:
            self.triax.connect()
            self.move_to_wavelength(wavelength, True)
            self.set_slit_size(self.slitsize)
        self.testheader["MONOTYPE"] = "Triax180"


    def get_headers(self):
        """
        Fills image header dictionaries for current setup.
        """
        #CCD operating conditions header
        self.opheader = self.reb.get_operating_header()

        self.opheader["V_BSS"] = "{:.2f}".format(self.bss.getOutputVoltage())
        # gives only current at this time, might upgrade to get measures during exposure
        self.opheader["I_BSS"] = "{:.2f}".format(self.bss.getCurrent())

        #need to add image format header, instruments header, optional sequencer header
        try:
            wavelength = self.triax.getWavelength()
        except:
            wavelength = 0.0
        self.primeheader["MONOWL"] = wavelength
        self.testheader["MONOWL"] = wavelength
