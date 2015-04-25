#
# LSST / LPNHE
# Author: Claire Juramy from original by Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""
import py.camera.generic.reb as reb
import fpga0
import time

# =======================================================================

class REB1(reb.REB):

    xmldir = "/home/lsst/py/camera/reb1/"

    # ===================================================================

    def __init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0]):
        reb.REB.__init__(self, reb_id, ctrl_host, stripe_id)
        self.fpga = fpga0.FPGA0(ctrl_host, reb_id)  # overwrites fpga from superclass

   # --------------------------------------------------------------------

    def REBpowerup(self):
        """
        Operations after powering the REB
        """
        #specific to REB1
        self.cabac_reset()

        self.load_sequencer()
        #sets the default sequencer clock states to 0
        self.fpga.send_function(0, fpga0.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

        print("REB ready to connect to CCD")

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """
        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.send_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG": 3.5}
        self.send_cabac_config(og)

        time.sleep(1)

        #sets clock rails
        dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
        self.fpga.set_clock_voltages(dacs)

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.send_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate
        for stripe in self.stripes:
            self.fpga.set_current_source(0xfff, stripe)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.fpga.send_function(0, self.seq.get_function(0))

        time.sleep(0.1)

        #now is the time to the backsubstrate voltage (elsewhere)
        print("CCD start-up sequence complete on REB, ready for Back Substrate.")

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """
        self.wait_end_sequencer()
        #Back-substrate first
        print("Back Substrate must be shut down before this.")
        time.sleep(3)

        #current source to 0
        for stripe in self.stripes:
            self.fpga.set_current_source(0, stripe)

        time.sleep(0.5)

        #clock states to 0
        self.fpga.send_function(0, fpga0.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))
        #currents on CABAC clocks to 0
        self.send_cabac_config({"IC": 0})
        #clock rails to 0
        self.fpga.set_clock_voltages({"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0})

        time.sleep(1)

        #OG to 0
        self.send_cabac_config({"OG": 0})

        time.sleep(1)

        #drains to 0
        self.send_cabac_config({"OD": 0, "GD": 0, "RD": 0})

        print("CCD shutdown complete")

   # --------------------------------------------------------------------

    def get_cabac_config(self):
        """
        read CABAC configuration.
        """
        for stripe in self.stripes:
            self.fpga.get_cabac_config(stripe)

    # --------------------------------------------------------------------

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
        for stripe in self.stripes:
            for param in iter(params):
                self.fpga.set_cabac_value(param, params[param], stripe)

            self.fpga.send_cabac_config(stripe)

            time.sleep(0.1)

            self.fpga.get_cabac_config(stripe)

            for param in iter(params):
                self.fpga.check_cabac_value(param, params[param], stripe)

    # --------------------------------------------------------------------

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        for stripe in self.stripes:
            self.fpga.reset_cabac(stripe)

        time.sleep(0.1)

        self.get_cabac_config()




