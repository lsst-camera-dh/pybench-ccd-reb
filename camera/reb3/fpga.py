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

    supplies = ['DREB', '7V', 'VDDCLK', 'VDDOD']
    clock_conv = 0.00357  # conversion for DAC (V/LSB)
    bias_conv = 0.00725  # conversion for alternative biases
    od_conv = 0.0195  # placeholder for alternative OD
    og_conv = 0.00122  # placeholder for alternative OG
    # TODO: replace with REB3 values
    n_sensors_boardtemp = 9  # 10 in REB2, only 9 in REB3 ?

    # mapping of clock rail settings
    clockmap = {"SL": 2, "SL_S": 1, "SU": 0, "PL": 5, "PL_S": 4, "PU": 3, "RGL": 0x12, "RGU": 0x11,"RGL_S": 0x10}

    # list of acceptable parameters for REB commands
    params = ["OD", "GD", "RD", "OG", 'CS',
              "SL", "SU", "RGL", "RGU", "PL", "PU"]
    groups = {'CLOCKS': ["SL", "SU", "RGL", "RGU", "PL", "PU"],
              'CLK_L': ["SL", "RGL", "PL"],
              'CLK_U': ["SU", "RGU", "PU"],
              'BIASES': ["OD", "GD", "RD", "OG"]}
    # list of DACs to be set
    dacparams = ["OD0", "GD0", "RD0", "OG0", 'OG_S0', 'CS0',
                 "OD1", "GD1", "RD1", "OG1", 'OG_S1', 'CS1',
                 "OD2", "GD2", "RD2", "OG2", 'OG_S2', 'CS2',
                 "SL", 'SL_S', "SU", "RGL", 'RG_S', "RGU", "PL", 'PL_S', "PU"]

    # mapping of slow ADC (mux8chan, adcmux)
    # last digit of parameter name is always the stripe
    adcmap = {'T_ASPT_0': (0, 2), 'T_ASPB_0': (0, 2),
              'T_ASPT_1': (0, 6), 'T_ASPB_1': (0, 7),
              'T_ASPT_2': (0, 10), 'T_ASPB_2': (0, 11),
              'CS_T0_0': (0, 0), 'CS_B0_0': (0, 1),
              'CS_T1_0': (1, 0), 'CS_B1_0': (1, 1),
              'CS_T2_0': (2, 0), 'CS_B2_0': (2, 1),
              'CS_T3_0': (3, 0), 'CS_B3_0': (3, 1),
              'CS_T4_0': (4, 0), 'CS_B4_0': (4, 1),
              'CS_T5_0': (5, 0), 'CS_B5_0': (5, 1),
              'CS_T6_0': (6, 0), 'CS_B6_0': (6, 1),
              'CS_T7_0': (7, 0), 'CS_B7_0': (7, 1),
              'CS_T0_1': (0, 4), 'CS_B0_1': (0, 5),
              'CS_T1_1': (1, 4), 'CS_B1_1': (1, 5),
              'CS_T2_1': (2, 4), 'CS_B2_1': (2, 5),
              'CS_T3_1': (3, 4), 'CS_B3_1': (3, 5),
              'CS_T4_1': (4, 4), 'CS_B4_1': (4, 5),
              'CS_T5_1': (5, 4), 'CS_B5_1': (5, 5),
              'CS_T6_1': (6, 4), 'CS_B6_1': (6, 5),
              'CS_T7_1': (7, 4), 'CS_B7_1': (7, 5),
              'CS_T0_2': (0, 8), 'CS_B0_2': (0, 9),
              'CS_T1_2': (1, 8), 'CS_B1_2': (1, 9),
              'CS_T2_2': (2, 8), 'CS_B2_2': (2, 9),
              'CS_T3_2': (3, 8), 'CS_B3_2': (3, 9),
              'CS_T4_2': (4, 8), 'CS_B4_2': (4, 9),
              'CS_T5_2': (5, 8), 'CS_B5_2': (5, 9),
              'CS_T6_2': (6, 8), 'CS_B6_2': (6, 9),
              'CS_T7_2': (7, 8), 'CS_B7_2': (7, 9),
              'OD_0': (12, 0), 'OD_1': (12, 5), 'OD_2': (13, 3),
              'OG_0': (12, 1), 'OG_1': (12, 6), 'OG_2': (13, 4),
              'RD_0': (12, 2), 'RD_1': (12, 7), 'RD_2': (13, 5),
              'GD_0': (12, 3), 'GD_1': (13, 0), 'GD_2': (13, 6),
              'ADC5V_0': (12, 4), 'ADC5V_1': (13, 1), 'ADC5V_2': (13, 7),
              'REF2V5_1': (13, 2)
              }

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2):
        FPGA.__init__(self, ctrl_host, reb_id)
        # declare two ASPICs for each stripe even if they will not be used
        self.aspics = {}
        self.aspics['top'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]
        self.aspics['bottom'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]

        self.dacs = {}
        for param in self.dacparams:
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

        # shift: L output will follow positive dac minus (factor tbc) shift dac
        for key in voltages:
            if key in self.groups['CLK_L']:
                keyshift = key+'_L'
                if voltages[key] > 0:
                    self.dacs[key] = int(voltages[key] / self.clock_conv) & 0xfff
                    self.dacs[keyshift] = 0
                else:
                    self.dacs[key] = 0
                    self.dacs[keyshift] = int(-voltages[key] / self.clock_conv) & 0xfff
                    # TODO: check factor for shift (should be 1 on REB3)

                self.write(0x400000, self.dacs[key] + (self.clockmap[key] << 12))
                self.write(0x400000, self.dacs[keyshift] + (self.clockmap[keyshift] << 12))
            elif key in self.groups['CLK_U']:
                self.dacs[key] = int(voltages[key] / self.clock_conv) & 0xfff
                self.write(0x400000, self.dacs[key] + (self.clockmap[key] << 12))
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

        # activates DAC outputs
        self.write(0x400001, 1)

    def get_clock_voltages(self):
        """
        No readback available, using values stored in fpga object.
        """
        orderkeys = self.groups['CLOCKS']
        dictvalues = {}
        dictcomments = {}

        for key in self.groups['CLK_L']:
            # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.serial_conv)
            dictvalues[key] = (self.dacs[key] - self.dacs[key + "_S"]) * self.clock_conv
            dictcomments[key] = '[V] %s low clock rail voltage' % key
            #TODO: check appropriate factor for shift
        for key in self.groups['CLK_U']:
            dictvalues[key] = self.dacs[key]* self.clock_conv
            dictcomments[key] = '[V] %s high clock rail voltage' % key

        return MetaData(orderkeys, dictvalues, dictcomments)

    # ----------------------------------------------------------

    def set_current_source(self, current, s=0):
        """
        Sets current source DAC value for the given stripe.
        The same FPGA registers are also used to write OD and other biases, see set_bias_voltages()
        :type s: int
        :type current: int
        :param current: integer value of CD DAC
        :param s: stripe
        :return:
        """
        self.check_location(s)
        dacaddress = 0x400100 + (s << 4)
        key = "I_OS"
        dackey = key + '%s' % s
        outputnum = 5

        self.dacs[dackey] = current & 0xfff
        self.write(dacaddress, self.dacs[dackey] + (outputnum << 12))

        #activates DAC output
        self.write(0x400001 + (s << 4), 1)

    def get_current_source(self, s):
        """
        No readback available, using values stored in fpga object.
        """

        self.check_location(s)
        key = "I_OS"
        dackey = "I_OS" + '%s' % s

        orderkeys = [key]
        dictvalues = {}
        dictcomments = {}

        dictvalues[key] = self.dacs[dackey]
        dictcomments[key] = '[ADU] %s CS gate current setting' % key

        return MetaData(orderkeys, dictvalues, dictcomments)

    # ----------------------------------------------------------

    def enable_bss(self, connect):
        """
        Switches the Back Substrate Bias connection to the CCD.
        :param connect: bool
        :return:
        """
        # TODO: check if the same register is used for REB3
        if connect:
            self.write(0xD00000, 1)
        else:
            self.write(0xD00000, 0)

    # ----------------------------------------------------------

    def set_bias_voltages(self, biases, s):
        """
        Sets the DC bias voltages.
        :type s: int
        :param biases: dict
        :param s: stripe
        :return:
        """
        outputnum = {"GD": 0, "OD": 1, "OG": 3, "OG_S": 2, "RD": 4}
        # OG seen by CCD will be the difference OG-OGS (factor to be checked)

        self.check_location(s)
        dacaddress = 0x400100 + (s << 4)

        for key in biases:
            dackey = key + '%s' % s
            if key in ["GD", "RD"]:
                self.dacs[dackey] = int(biases[key] / self.bias_conv) & 0xfff
                self.write(dacaddress, self.dacs[dackey] + (outputnum[key] << 12))
            elif key == "OD":
                self.dacs[dackey] = int(biases[key] / self.od_conv) & 0xfff
                self.write(dacaddress, self.dacs[dackey] + (outputnum[key] << 12))
            elif key == "OG":
                dackeyshift = "OG_S" + '%s' % s
                if biases[key] > 0:
                    self.dacs[dackey] = int(biases[key] / self.og_conv) & 0xfff
                    self.dacs[dackeyshift] = 0
                else:
                    self.dacs[dackey] = 0
                    self.dacs[dackeyshift] = int(-biases[key] / self.og_conv) & 0xfff
                self.write(dacaddress, self.dacs[dackey] + (outputnum[key] << 12))
                self.write(dacaddress, self.dacs[dackeyshift] + (outputnum["OG_S"] << 12))
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

        # activates DAC outputs
        self.write(0x400001 + (s << 4), 1)

    def get_bias_voltages(self, s):
        """
        No readback, using values stored in fpga object.
        :type s: int
        :param s: stripe
        """
        self.check_location(s)
        orderkeys = self.groups['BIASES']
        dictvalues = {}
        dictcomments = {}

        for key in self.groups['BIASES']:
            dackey = key + '%s' % s
            if key == 'OG':
                dackeyshift = "OG_S" + '%s' % s
                dictvalues[key] = (self.dacs[dackey] - self.dacs[dackeyshift]) * self.og_conv

            #TODO: check appropriate factor for shift
            if key == 'OD':
                dictvalues[key] = self.dacs[dackey]* self.od_conv
            else:
                dictvalues[key] = self.dacs[dackey]* self.bias_conv
            dictcomments[key] = '[V] %s voltage setting' % key

        return MetaData(orderkeys, dictvalues, dictcomments)


    def check_location(self, s, loc=3):
        if s not in [0, 1, 2]:
            raise ValueError("Invalid REB stripe (%d)" % s)
        if loc not in [1, 2, 3]:
            raise ValueError("Invalid Location code (%d)" % loc)
        return True

    # ----------------------------------------------------------

    def get_dacs_config(self, s, check=True):  # stripe 's'
        """
        Output for header.
        """
        #TODO: add any missing data
        config = self.get_input_voltages_currents()
        config.update(self.get_clock_voltages())
        config.update(self.get_bias_voltages(s))
        config.update(self.get_current_source(s))
        config.update(self.slow_adc_stripe(s))

        return config

    # ----------------------------------------------------------

    def slow_adc_readmux(self, extmux, adcmux):
        """
        Triggers reading of slow ADC pointed at the given address
        :param extmux: address on external 8-channel mux
        :param adcmux: address on internal 16-channel mux
        :return: int
        """
        # includes enable bit on 8-channel mux
        self.write(0x600101, ((8 + (extmux & 7)) << 16) + (adcmux & 0xf))

        raw = self.read(0x601010, 1)[0x601010]
        value = raw & 0xfff
        checkextmux = (raw >> 20) & 7
        checkadcmux = (raw >> 12) & 0xf
        if (checkextmux != extmux) or (checkadcmux != adcmux):
            print('Warning: mismatch in slow ADC read %d, %d' % (checkextmux, checkadcmux))

        return value

    def aspic_temperature_read(self):
        """
        Reads all the ASPIC temperature sensors.
        :return: MetaData
        """
        self.write(0x600100, 1)

        #time.sleep(0.01)

        temps = self.read(0x601000, 6)
        orderkeys = ['T_ASPT_0', 'T_ASPB_0', 'T_ASPT_1', 'T_ASPB_1', 'T_ASPT_2', 'T_ASPB_2']
        dictvalues = {}
        dictcomments = {}

        for iaddress, key in enumerate(orderkeys):
            dictvalues[key] = temps[0x601000 + iaddress]
            dictcomments[key] = '[ADU] ASPIC temperature sensor %s' % key
            # TODO: conversion to volts, then to temperature

        return MetaData(orderkeys, dictvalues, dictcomments)

    def slow_adc_read(self, param):
        """
        Reads any parameter by name.
        :param param:
        :return:
        """
        extmux, adcmux = self.adcmap[param]

        return self.slow_adc_readmux(extmux, adcmux)

    def slow_adc_stripe(self, s):
        """
        Reads all slow ADC values relevant to a given stripe.
        :param s: stripe
        :return:
        """
        self.check_location(s)

        orderkeys = []
        dictvalues = {}
        dictcomments = {}

        for key in self.adcmap:
            # last digit of parameter name is always the stripe
            if key[-1] == '%d' % s:
                value = self.slow_adc_read(key)
                orderkeys.append(key)
                dictvalues[key] = value
                dictcomments[key] = '[ADU] %s read through slow ADC' % key

        return MetaData(orderkeys, dictvalues, dictcomments)

    # ----------------------------------------------------------
    #TODO: heaters (not urgent ?)
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
