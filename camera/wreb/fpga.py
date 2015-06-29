#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA new version (REB2/WREB)
#
#
from lsst.camera.generic.fpga import *
import time

import cabac
import aspic


# # -----------------------------------------------------------------------

class FPGA1(FPGA):
    # ctrl_host = "lpnws4122"
    # reb_id = 2

    clock_conv = 0.00357  # conversion for DAC (V/LSB)
    bias_conv = 0.00725  # conversion for alternative biases
    od_conv = 0.0195  # placeholder for alternative OD
    og_conv = 0.00122  # placeholder for alternative OG
    VddOD = 14  # high voltage power supply to CABAC if used for biases

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2):
        FPGA.__init__(self, ctrl_host, reb_id)
        # declare two CABACs and two ASPICs for each stripe even if they will not be used
        # (at least we will want to initialize to 0)
        self.cabac_top = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.cabac_bottom = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.aspic_top = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]
        self.aspic_bottom = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]
        self.dacs = {}

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

    # ----------------------------------------------------------
    def cabac_power(self, enable):
        """
        Enables/disables power to CABAC low voltage VEE and power supplies, powered in that order for CABAC safety.
        VddOD needs to be powered on before / shut down after.
        The clock rails need to be done after power-on/ before power-down, in the higher level function.
        :param enable: bool
        :return:
        """
        if enable:
            # enable VEE and then all low voltages
            self.write(0xD00001, 0x4)  # VEE (CABAC substrate) set to V_CLK_L (low clock power supply) if connected
            time.sleep(0.2)
            self.write(0xD00001, 0x1F)
        else:
            # reverse order
            self.write(0xD00001, 0x4)
            time.sleep(0.2)
            self.write(0xD00001, 0)

    def check_location(self, s, loc=3):
        if s not in [0, 1, 2]:
            raise ValueError("Invalid REB stripe (%d)" % s)
        if loc not in [1, 2, 3]:
            raise ValueError("Invalid Location code (%d)" % loc)
        return True

    def get_cabac_config(self, s, check=True):  # stripe 's'
        """
        read CABAC configuration for stripe <s>,
        store it in the CABAC objects and the header dict.
        """

        self.check_location(s)

        topconfig = {}
        bottomconfig = {}

        for address in range(22):
            regaddress = address << 16
            # send for reading top CABAC
            self.write_spi(0x500000, s, 2, regaddress)
            # read answer to dict
            #time.sleep(0.05)
            topconfig[address] = self.read(0x500010 + s, 1)[0x500010 + s]
            # send for reading bottom CABAC
            self.write_spi(0x500000, s, 1, regaddress)
            # read answer to dict
            #time.sleep(0.05)
            bottomconfig[address] = self.read(0x500010 + s, 1)[0x500010 + s]

        self.cabac_top[s].read_all_registers(topconfig, check)
        self.cabac_bottom[s].read_all_registers(bottomconfig, check)

        keyst, configt, comt = self.cabac_top[s].get_header("%dT" % s)
        keysb, configb, comb = self.cabac_bottom[s].get_header("%dB" % s)

        config = MetaData(keyst, configt, comt, 'CABACS')
        config.update_ordered(keysb, configb, comb)

        return config

    # ----------------------------------------------------------

    def get_cabac_value(self, reg, s, loc):  # stripe 's'
        """
        Low-level readback of CABAC configuration for a single register.
        """
        self.check_location(s, loc)

        self.write_spi(0x500000, s, loc, reg, False)
        value = self.read(0x500010 + s, 1)[0x500010 + s]

        return value

    def set_cabac_value(self, param, value, s=0, loc=3, check=True):
        """
        Sets the CABAC parameter at the appropriate stripe and location (1 for bottom, 2 for top, 3 for both).
        Default values for retro-compatibility.
        :return: bool
        """
        self.check_location(s, loc)

        if loc == 1 or loc == 3:
            # bottom CABAC
            if self.cabac_bottom[s].check_bias_safety(param, value):
                regs = self.cabac_bottom[s].set_cabac_fromstring(param, value)
                for reg in regs:
                    self.write_spi(0x500000, s, 1, reg, True)
                    if check:
                        value_int = self.get_cabac_value(reg, s, 1)
                        if value_int != self.cabac_bottom[s].get_cabac_fromstring(param):
                            print("Warning: unexpected value for %s: %d" % (param, value_int))
            else:
                return False

        if loc == 2 or loc == 3:
            # top CABAC
            if self.cabac_top[s].check_bias_safety(param, value):
                regs = self.cabac_top[s].set_cabac_fromstring(param, value)
                for reg in regs:
                    self.write_spi(0x500000, s, 2, reg, True)
                    if check:
                        value_int = self.get_cabac_value(reg, s, 2)
                        if value_int != self.cabac_top[s].get_cabac_fromstring(param):
                            print("Warning: unexpected value for %s: %d" % (param, value_int))
            else:
                return False
        return True

    # ----------------------------------------------------------

    def reset_cabac(self, s=0):  # stripe 's'
        """
        Use CABAC reset for stripe s
        """
        self.check_location(s)

        self.write(0x500001, s)  # starts the CABAC reset

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

        self.aspic_top[s].read_all_registers(topconfig, True)
        self.aspic_bottom[s].read_all_registers(bottomconfig, True)

        keyst, configt, comt = self.aspic_top[s].get_header("%dT" % s)
        keysb, configb, comb = self.aspic_bottom[s].get_header("%dB" % s)

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
            reg = self.aspic_bottom[s].set_aspic_fromstring(param, value)
            self.write_spi(0xB00000, s, 1, reg, True)
        if loc == 2 or loc == 3:
            # top ASPIC
            reg = self.aspic_top[s].set_aspic_fromstring(param, value)
            self.write_spi(0xB00000, s, 2, reg, True)

    def apply_aspic_config(self, s=0, loc=3):
        """
        Apply all stored settings to the ASPIC(s) designed by the stripe s (amongst 0,1,2) and the location
        (1 for bottom, 2 for top, 3 for both).
        """
        self.check_location(s, loc)

        if loc == 1 or loc == 3:
            # bottom ASPIC
            AspicData = self.aspic_bottom[s].write_all_registers()
            for address in range(2):
                self.write_spi(0xB00000, s, 1, AspicData[address], True)
        if loc == 2 or loc == 3:
            # top ASPIC
            AspicData = self.aspic_top[s].write_all_registers()
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

