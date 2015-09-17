#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA new version (REB2/WREB)
#
#
from lsst.camera.generic.fpga import *
import time

import lsst.camera.generic.aspic as aspic


# # -----------------------------------------------------------------------

class FPGA2(FPGA):
    # ctrl_host = "lpnws4122"
    # reb_id = 2

    clock_conv = 0.00357  # conversion for DAC (V/LSB)
    bias_conv = 0.00725  # conversion for alternative biases
    od_conv = 0.0195  # placeholder for alternative OD
    og_conv = 0.00122  # placeholder for alternative OG
    # TODO: replace with REB3 values

    # list of acceptable parameters for REB DACs
    params = ["OD", "GD", "RD", "OG", 'OG_S', 'CS',
              "SL", "SU", "RGL", "RGU", "PL", "PU",
              "SL_S", "SU_S", "RGL_S", "RGU_S", "PL_S", "PU_S"]
    groups = {'CLOCKS': ["SL", "SU", "RGL", "RGU", "PL", "PU",
              "SL_S", "SU_S", "RGL_S", "RGU_S", "PL_S", "PU_S"],
              'BIASES': ["OD", "GD", "RD", "OG", 'OG_S']}

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2):
        FPGA.__init__(self, ctrl_host, reb_id)
        # declare two ASPICs for each stripe even if they will not be used
        self.aspics = {}
        self.aspics['top'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]
        self.aspics['bottom'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]

        self.dacs = {}
        for param in self.params:
            self.dacs[param] = 0

    # --------------------------------------------------------------------

    def sigmadelta_spi(self, rw, address, data):
        """
        Communication to the sigma-delta ADC for CCD temperature sensors.
        :param rw: bool
        :param address: int
        :param data: int
        :return: int
        """
        # To be checked: there are several bugs in the documentation
        code = 0
        if rw:
            code += (1 << 19)
        code += ((address & 7) << 16)
        code += (data & 0xffff)
        self.write(0x700000, code)
        time.sleep(0.05)

        answer = self.read(0x700001, 1)[0x700001]
        return answer

    # --------------------------------------------------------------------

    def increment(self, offset=0):
        """
        Send the command to increment the ADC sampling time by 1 cycle after
        each ADC trigger.
        """
        self.write(0x330000, 1)
        self.write(0x330001, offset & 0xff)

    def stop_increment(self):
        """
        Send the command to stop incrementing the ADC sampling time and reset the shift.
        """
        self.write(0x330000, 0)
        self.write(0x330001, 0)

    # ----------------------------------------------------------

    def set_clock_voltages(self, voltages):
        """
        Sets voltages as defined in the input dictionary, keeps others as previously defined.
        Note that order in which they are programmed does not matter as they are all activated together.
        """
        #values to be set in the register for each output (shift will be +1)
        outputnum = {"SL": 0, "SU": 2, "RGL": 4, "RGU": 6, "PL": 16, "PU": 18}
        # shift: output will follow positive dac minus (factor tbc) shift dac
        for key in iter(voltages):
            key_shift = key + "_S"
            if key in ["SL", "SU", "RGL", "RGU", "PL", "PU"]:
                if voltages[key] > 0:
                    self.dacs[key] = int(voltages[key] / self.clock_conv) & 0xfff
                    self.dacs[key_shift] = 0
                else:
                    self.dacs[key] = 0
                    self.dacs[key_shift] = int(-voltages[key] / self.clock_conv) & 0xfff
            # TODO: check factor for shift
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

            self.write(0x400000, self.dacs[key] + (outputnum[key] << 12))
            # shift at address+1
            self.write(0x400000, self.dacs[key_shift] + ((outputnum[key] + 1) << 12))

        # activates DAC outputs
        self.write(0x400001, 1)

    # ----------------------------------------------------------

    def get_clock_voltages(self):
        """
        No readback available, using values stored in fpga object.
        """
        fitsheader = {}
        for key in ["SL", "SU", "RGL", "RGU", "PL", "PU"]:
            # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.serial_conv)
            fitsheader[key] = (self.dacs[key] - self.dacs[key + "_S"]) * self.clock_conv
            #TODO: check appropriate factor for shift

        return fitsheader

    # ----------------------------------------------------------

    def set_current_source(self, currents, ccdnum=0):
        """
        Sets current source DAC value for given CCD (0, 1, 2).
        The same FPGA registers are also used to write OD and FS if used, see set_bias_voltages()
        """

        key = "I_OS"

        if key in currents:
            self.dacs[key] = currents[key] & 0xfff
        else:
            raise ValueError(
                "No key found for current source (%s), could not be set." % key)

        self.write(0x400010, self.dacs[key] + (ccdnum << 12))

        #activates DAC output
        self.write(0x400011, 1)

    # ----------------------------------------------------------

    def get_current_source(self):
        """
        No readback available, using values stored in fpga object.
        """

        key = "I_OS"

        return {key: self.dacs[key]}

    def enable_bss(self, connect):
        """
        Switches the Back Substrate Bias connection to the CCD.
        :param connect: bool
        :return:
        """
        if connect:
            self.write(0xD00000, 1)
        else:
            self.write(0xD00000, 0)

    # ----------------------------------------------------------

    def set_bias_voltages(self, biases):
        """
        For WREB: sets the alternative bias voltages.
        :param biases: dict
        :return:
        """
        outputnum = {"GD": 0, "RD": 1, "OG": 2, "OGS": 3}
        # OG seen by CCD will be the difference OG-OGS
        outputnum1 = {"FSB": 3, "OD": 6}
        for key in iter(biases):
            if key in ["GD", "RD"]:
                self.dacs[key] = int(biases[key] / self.bias_conv) & 0xfff
                self.write(0x400100, self.dacs[key] + (outputnum[key] << 12))
            elif key == "OD":
                self.dacs[key] = int(biases[key] / self.od_conv) & 0xfff
                self.write(0x400010, self.dacs[key] + (outputnum1[key] << 12))
            elif key == "OG":
                if biases[key] > 0:
                    self.dacs[key] = int(biases[key] / self.og_conv) & 0xfff
                    self.dacs["OGS"] = 0
                else:
                    self.dacs[key] = 0
                    self.dacs["OGS"] = int(-biases[key] / self.og_conv) & 0xfff
                self.write(0x400100, self.dacs[key] + (outputnum[key] << 12))
                self.write(0x400100, self.dacs["OGS"] + (outputnum["OGS"] << 12))
            elif key == "FSB":
                self.dacs[key] = int(biases[key] / self.clock_conv) & 0xfff
                self.write(0x400010, self.dacs[key] + (outputnum1[key] << 12))
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

        # activates DAC outputs
        self.write(0x400011, 1)
        self.write(0x400101, 1)

    def set_OD_voltage(self, value):
        """
        Sets OD voltage alone. Useful when using it as CABAC high voltage power supply.
        Currently disabled on the WREB hardware.
        :param value: float
        :return:
        """
        self.dacs["OD_CTRL"] = int(value / self.od_conv) & 0xfff
        self.write(0x400010, self.dacs["OD_CTRL"] + (6 << 12))
        # activates DAC outputs
        self.write(0x400011, 1)

    def check_location(self, s, loc=3):
        if s not in [0, 1, 2]:
            raise ValueError("Invalid REB stripe (%d)" % s)
        if loc not in [1, 2, 3]:
            raise ValueError("Invalid Location code (%d)" % loc)
        return True

    def get_dacs_config(self, s, check=True):  # stripe 's'
        """
        Output for header.
        """
        #TODO
        config = MetaData(keyst, configt, comt, 'CABACS')
        config.update_ordered(keysb, configb, comb)

        return config

    # ----------------------------------------------------------

    def get_aspic_config(self, s=0, check=False):
        """
        Read ASPIC configurations for the given stripe and updates objects in class.
        If check is true then it checks that the readback is the same as the expected value.
        :param s:
        """
        self.check_location(s)

        topconfig = {}
        bottomconfig = {}

        for address in range(3):
            # send for reading top ASPIC
            self.write_spi(0xB00000, s, 2, address << 16)
            # read answer
            topconfig[address] = self.read(0xB00010 + s, 1)[0xB00010 + s]
            # send for reading bottom ASPIC
            self.write_spi(0xB00000, s, 1, address << 16)
            # read answer
            bottomconfig[address] = self.read(0xB00010 + s, 1)[0xB00010 + s]

        self.aspics['top'][s].read_all_registers(topconfig, True)
        self.aspics['bottom'][s].read_all_registers(bottomconfig, True)

        keyst, configt, comt = self.aspics['top'][s].get_header("%dT" % s)
        keysb, configb, comb = self.aspics['bottom'][s].get_header("%dB" % s)

        config = MetaData(keyst, configt, comt, 'ASPICS')
        config.update_ordered(keysb, configb, comb)

        return config

    def set_aspic_value(self, param, value, s=0, loc=3):
        """
        Sets the ASPIC parameter at the given value on ASPICs of the given stripe at the given location and stores in
        object.
        """
        self.check_location(s, loc)

        if loc == 1 or loc == 3:
            # bottom ASPIC
            reg = self.aspics['bottom'][s].set_aspic_fromstring(param, value)
            self.write_spi(0xB00000, s, 1, reg, True)
        if loc == 2 or loc == 3:
            # top ASPIC
            reg = self.aspics['top'][s].set_aspic_fromstring(param, value)
            self.write_spi(0xB00000, s, 2, reg, True)

    def apply_aspic_config(self, s=0, loc=3):
        """
        Apply all stored settings to the ASPIC(s) designed by the stripe s (amongst 0,1,2) and the location
        (1 for bottom, 2 for top, 3 for both).
        """
        self.check_location(s, loc)

        if loc == 1 or loc == 3:
            # bottom ASPIC
            AspicData = self.aspics['bottom'][s].write_all_registers()
            for address in range(2):
                self.write_spi(0xB00000, s, 1, AspicData[address], True)
        if loc == 2 or loc == 3:
            # top ASPIC
            AspicData = self.aspics['top'][s].write_all_registers()
            for address in range(2):
                self.write_spi(0xB00000, s, 2, AspicData[address], True)

    def reset_aspic(self, s=0):
        """
        Sends the reset command to the ASPICs of the appropriate stripe(s).
        :return:
        """
        self.check_location(s)

        self.write(0xB00001, s)

# TODO: ASIC temperature readouts

