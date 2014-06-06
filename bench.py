#! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import reb
import fpga
import time
import Keithley
import xmlrpclib


class Bench(object):
    """
    Internal representation of the full bench
    """

    def __init__(self):
        self.reb = reb.REB()
        self.bss = xmlrpclib.ServerProxy("http://lpnlsst:8087/")
        self.bss.connect()
        # implementation with remote control
        # other instruments ?

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
        dacCS["I_OS"] = 0xfff
        self.reb.set_dacs(dacCS)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.reb.load_function(0, fpga.Function(name = "default state",
                                                timelengths = {0:2, 1:0},
                                                outputs = {0:0x6bc, 1:0}))


        time.sleep(1)

        #starts Keithley backsubstrate voltage
        self.config_bss(40)
        self.bss.setVoltageOperate(1)

    def shutdown(self):
        """
        Sequence to shut down the CCD safely
        """
        
        #Back-substrate first
        self.bss.setVoltageOperate(0)
        time.sleep(1)

        while abs(volt) > 0.1:
            volt = self.bss.getVoltage()

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
            range = 50
        else:
            range = 500
        self.bss.selectOutputVoltageRange(range, 2.5e-5)
        
        self.bss.setOutputVoltage(voltage)

        self.bss.zeroCorrect()
        self.bss.selectCurrent(2e-5)

    def get_headers(self):
        """
        Fills image header dictionaries for current setup.
        """
        #CCD operating conditions header
        opheader = self.reb.get_operating_header()

        self.bss.getOutputVoltage()
        self.bss.getCurrent()  # gives only current at this time, might upgrade to get measures during exposure
        opheader["V_BSS"] = "{:.2f}".format(self.bss.volt)
        opheader["I_BSS"] = "{:.2f}".format(self.bss.current)

        #need to add image format header, instruments header

