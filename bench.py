#! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import reb
import fpga
import time

class Bench(object):
    """
    Internal representation of the full bench
    """

    def __init__(self):
        self.reb = reb.REB()
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


        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.reb.set_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate


        #rewrite default state of sequencer (to avoid reloading functions)
        self.reb.load_function(0, fpga.Function(name = "default state",
                                                timelengths = {0:2, 1:0},
                                                outputs = {0:0x6bc, 1:0}))


        time.sleep(1)

        #starts Keithley backsubstrate voltage

