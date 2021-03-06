#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA new version (REB2/WREB/REB3)
#
#
from lsst.camera.generic.fpga import *
import time

import lsst.camera.generic.aspic as aspic


# # -----------------------------------------------------------------------

class FPGA3(FPGA):
    # ctrl_host = "lpnws4122"
    # reb_id = 2

    supplies = ['DREB', '7V', 'VDDCLK', 'VDDOD']
    n_sensors_boardtemp = 10

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
                 "SL", 'SL_S', "SU", "RGL", 'RGL_S', "RGU", "PL", 'PL_S', "PU"]

    # mapping of clock rail settings
    clockmap = {"SL": 2, "SL_S": 1, "SU": 0, "PL": 5, "PL_S": 4, "PU": 3, "RGL": 0x12, "RGL_S": 0x11,"RGU": 0x10}
    # default conversion factors for clock DAC (V/LSB):
    clock_conv = 0.00425
    # mapping for clock conversions
    convertclocks = {"SL": clock_conv,
                     "SL_S": clock_conv,
                     "SU": 0.00426758,
                     "PL": clock_conv,
                     "PL_S": 0.00306,
                     "PU": 0.00421875,
                     "RGL": clock_conv,
                     "RGL_S": 0.00268,
                     "RGU": 0.00425293}

    # mapping for bias conversions
    convertbiases = {"OD": 0.00880585,
                     "GD": 0.0088833,
                     "RD": 0.0061035,
                     "OG": 0.00240885,
                     'OG_S': 0.0012561}

    # mapping of slow ADC (mux8chan, adcmux)
    # different for REB3 and REB4
    # last digit of parameter name is always the stripe
    hardwareadcmap = {
        'REB3': {'T_ASPT_0': (0, 2), 'T_ASPB_0': (0, 3),
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
              'OD_0': (1, 12), 'OD_1': (6, 12), 'OD_2': (4, 13),
              'OG_0': (2, 12), 'OG_1': (7, 12), 'OG_2': (5, 13),
              'RD_0': (3, 12), 'RD_1': (0, 13), 'RD_2': (6, 13),
              'GD_0': (0, 12), 'GD_1': (5, 12), 'GD_2': (3, 13),
              'ADC5V_0': (4, 12), 'ADC5V_1': (1, 13), 'ADC5V_2': (7, 13),
              'REF2V5_1': (2, 13)
              },
        'REB4':{'T_ASPT_0': (0, 2, 0), 'T_ASPB_0': (0, 3, 0),
              'T_ASPT_1': (0, 6, 0), 'T_ASPB_1': (0, 7, 0),
              'T_ASPT_2': (0, 2, 1), 'T_ASPB_2': (0, 3, 1),
              'CS_T0_0': (0, 0, 0), 'CS_B0_0': (0, 1, 0),
              'CS_T1_0': (1, 0, 0), 'CS_B1_0': (1, 1, 0),
              'CS_T2_0': (2, 0, 0), 'CS_B2_0': (2, 1, 0),
              'CS_T3_0': (3, 0, 0), 'CS_B3_0': (3, 1, 0),
              'CS_T4_0': (4, 0, 0), 'CS_B4_0': (4, 1, 0),
              'CS_T5_0': (5, 0, 0), 'CS_B5_0': (5, 1, 0),
              'CS_T6_0': (6, 0, 0), 'CS_B6_0': (6, 1, 0),
              'CS_T7_0': (7, 0, 0), 'CS_B7_0': (7, 1, 0),
              'CS_T0_1': (0, 4, 0), 'CS_B0_1': (0, 5, 0),
              'CS_T1_1': (1, 4, 0), 'CS_B1_1': (1, 5, 0),
              'CS_T2_1': (2, 4, 0), 'CS_B2_1': (2, 5, 0),
              'CS_T3_1': (3, 4, 0), 'CS_B3_1': (3, 5, 0),
              'CS_T4_1': (4, 4, 0), 'CS_B4_1': (4, 5, 0),
              'CS_T5_1': (5, 4, 0), 'CS_B5_1': (5, 5, 0),
              'CS_T6_1': (6, 4, 0), 'CS_B6_1': (6, 5, 0),
              'CS_T7_1': (7, 4, 0), 'CS_B7_1': (7, 5, 0),
              'CS_T0_2': (0, 0, 1), 'CS_B0_2': (0, 1, 1),
              'CS_T1_2': (1, 0, 1), 'CS_B1_2': (1, 1, 1),
              'CS_T2_2': (2, 0, 1), 'CS_B2_2': (2, 1, 1),
              'CS_T3_2': (3, 0, 1), 'CS_B3_2': (3, 1, 1),
              'CS_T4_2': (4, 0, 1), 'CS_B4_2': (4, 1, 1),
              'CS_T5_2': (5, 0, 1), 'CS_B5_2': (5, 1, 1),
              'CS_T6_2': (6, 0, 1), 'CS_B6_2': (6, 1, 1),
              'CS_T7_2': (7, 0, 1), 'CS_B7_2': (7, 1, 1),
              'OD_0': (1, 4, 1), 'OD_1': (6, 4, 1), 'OD_2': (4, 5, 1),
              'OG_0': (2, 4, 1), 'OG_1': (7, 4, 1), 'OG_2': (5, 5, 1),
              'RD_0': (3, 4, 1), 'RD_1': (0, 5, 1), 'RD_2': (6, 5, 1),
              'GD_0': (0, 4, 1), 'GD_1': (5, 4, 1), 'GD_2': (3, 5, 1),
              'ADC5V_0': (4, 4, 1), 'ADC5V_1': (1, 5, 1), 'ADC5V_2': (7, 5, 1),
              'REF2V5_1': (2, 5, 1),
              'PU': (0, 0, 2), 'PL': (0, 1, 2),
              'SU': (0, 2, 2), 'SL': (0, 3, 2),
              'RGU': (0, 4, 2), 'RGL': (0, 5, 2),
              'P12': (0, 6, 2), 'N12': (0, 7, 2)
              }
    }
    # conversion factor for slow ADC
    hardwareconvert = {'REB3': 0.0012207, 'REB4': (0.0012207, 0.0024414, 0.0024414)}

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2, hardware='REB3'):
        FPGA.__init__(self, ctrl_host, reb_id)
        # declare two ASPICs for each stripe even if they will not be used
        self.aspics = {}
        self.aspics['top'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]
        self.aspics['bottom'] = [aspic.ASPIC(), aspic.ASPIC(), aspic.ASPIC()]

        self.dacs = {}
        for param in self.dacparams:
            self.dacs[param] = 0
        self.hardware = hardware
        self.adcmap = self.hardwareadcmap[self.hardware]
        self.adcconvert = self.hardwareconvert[self.hardware]
        
    # --------------------------------------------------------------------

    def get_boardID(self):
        """
        Reads the REB serial number stored in a chip on the board.
        :rtype: string
        """
        self.write(0x800000, 1)  # starts REB SN acquisition
        time.sleep(0.01)
        regs = self.read(0x800001, 2)
        controlbits = regs[0x800002] >> 16
        if not controlbits & 1:
            print('Error code %d while reading the board serial number' % controlbits)
        SNstring = '0x%04x%08x' % (regs[0x800002] & 0xffff, regs[0x800001])

        return SNstring

    # --------------------------------------------------------------------

    def sigmadelta_spi(self, rnotw, address, data):
        """
        Communication to the sigma-delta ADC for CCD temperature sensors.
        :type rnotw: bool
        :type address: int
        :type data: int
        :rtype: int
        """

        code = 0
        if rnotw:
            code += (1 << 19)
        code += ((address & 7) << 16)
        code += (data & 0xffff)
        self.write(0x700000, code)
        time.sleep(0.05)

        if rnotw:
            answer = self.read(0x700001, 1)[0x700001]
        else:
            answer = code
        return answer

    def config_sigmadelta(self, channel, gain=3, continuous=True):
        """
        Configures the 24-bit sigma-delta ADC: readout mode, channel, gain
        :param continuous:
        :return:
        """

        if continuous:
            self.sigmadelta_spi(False, 1, 0xA)

        else:
            self.sigmadelta_spi(False, 1, 0x200A)

        # select channel and gain
        #currentconfig = self.sigmadelta_spi(True, 2, 0)
        newconfig = (gain << 8) + 0x10 + channel
        self.sigmadelta_spi(False, 2, newconfig)
        # power on current
        self.sigmadelta_spi(False, 5, 0x200)

    def read_sigmadelta(self, continuous=True):
        """
        Reads the data from the sigma-delta ADC.
        :return:
        """
        if continuous:
            # could wait here by watching RDY bit, probably not time-critical enough
            answer = self.sigmadelta_spi(True, 3, 0)
        else:
            # power up and perform single conversion
            self.sigmadelta_spi(False, 1, 0x200A)
            # read result
            answer = self.sigmadelta_spi(True, 3, 0)
        
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
                keyshift = key+'_S'
                if voltages[key] > 0:
                    self.dacs[key] = int(voltages[key] / self.convertclocks[key]) & 0xfff
                    self.dacs[keyshift] = 0
                else:
                    self.dacs[key] = 0
                    self.dacs[keyshift] = int(-voltages[key] / self.convertclocks[keyshift]) & 0xfff

                self.write(0x400000, self.dacs[key] + (self.clockmap[key] << 12))
                self.write(0x400000, self.dacs[keyshift] + (self.clockmap[keyshift] << 12))
            elif key in self.groups['CLK_U']:
                self.dacs[key] = int(voltages[key] / self.convertclocks[key]) & 0xfff
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
            dictvalues[key] = round(self.dacs[key] * self.convertclocks[key] \
                              - self.dacs[key + "_S"] * self.convertclocks[key + "_S"], 3)
            dictcomments[key] = '[V] %s low clock rail voltage' % key

        for key in self.groups['CLK_U']:
            dictvalues[key] = round(self.dacs[key]* self.convertclocks[key], 3)
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
        key = "CS"
        dackey = key + '%s' % s
        outputnum = 5

        self.dacs[dackey] = current & 0xfff
        self.write(dacaddress, self.dacs[dackey] + (outputnum << 12))

        #activates DAC output
        self.write(0x400101 + (s << 4), 1)

    def get_current_source(self, s, readback=False):
        """
        In REB3, we can read all channels from the slow ADC+mux, or just the stored value.
        """

        self.check_location(s)
        key = "CS"
        dackey = "CS" + '%s' % s

        orderkeys = [key]
        dictvalues = {}
        dictcomments = {}

        dictvalues[key] = self.dacs[dackey]
        dictcomments[key] = '[ADU] %s CS gate current setting' % dackey

        if readback:
            #cschannels = ['CS_T%d' % chan for chan in range(8)] + ['CS_B%d' % chan for chan in range(8)]
            cschannels =['CS_T0', 'CS_T1', 'CS_T2', 'CS_T3', 'CS_T4', 'CS_T5', 'CS_T6', 'CS_T7',
                         'CS_B0', 'CS_B1', 'CS_B2', 'CS_B3', 'CS_B4', 'CS_B5', 'CS_B6', 'CS_B7']
            for key in cschannels:
                adckey = key + '_%s' % s
                orderkeys.append(key)
                value = self.slow_adc_read(adckey)
                dictvalues[key] = value
                dictcomments[key] = '[mA] current in source %s'  % adckey

        return MetaData(orderkeys, dictvalues, dictcomments)

    # ----------------------------------------------------------

    def enable_bss(self, connect):
        """
        Switches the Back Substrate Bias connection to the CCD.
        :param connect: bool
        :return:
        """
        # TODO: put back if correction is done in FPGA/hardware
        if connect:
            self.write(0xD00000, 0)
        else:
            self.write(0xD00000, 1)

    # ----------------------------------------------------------

    def check_bias_safety(self, biases, s):
        """
        Checks that the proposed parameters are safe for the CCD, using saved values.
        :type biases: dict
        :type s: int
        :rtype: bool
        """
        # reads current configuration
        # TODO: (currently from object, could be from ADC)
        # not while latch-up mess with multiplexed bias values
        current = self.get_bias_voltages(s)
        # computes proposed configuration
        proposed = {}
        for param in self.groups['BIASES']:
            if param in biases:
                proposed[param] = biases[param]
            else:
                proposed[param] = current.values[param]

        # safety: OG<OD (add margin for rounding errors)
        if proposed['OD'] < proposed['OG'] - 0.2:
            print("Warning: proposed configuration has OG at %f, higher than OD at %f" % (proposed['OG'], proposed['OD']))
            return False

        # safety: OD-RD < 20 V, but preferably also OD>RD (add margin for rounding errors)
        if proposed['RD'] > proposed['OD'] + 0.2:
            print("Warning: proposed configuration has OD lower than RD")
            return False
        elif proposed['OD'] > proposed['RD'] + 20:
            print("Warning: proposed configuration has OD higher than RD + 20 V")
            return False

        return True

    def set_bias_voltages(self, biases, s):
        """
        Sets the DC bias voltages.
        :type s: int
        :param biases: dict
        :param s: stripe
        :return:
        """
        if not self.check_bias_safety(biases, s):
            raise ValueError('Trying to program an unsafe bias value')

        outputnum = {"GD": 0, "OD": 1, "OG": 3, "OG_S": 2, "RD": 4}
        # OG seen by CCD will be the difference OG-OGS (factor to be checked)

        self.check_location(s)
        dacaddress = 0x400100 + (s << 4)

        for key in biases:
            dackey = key + '%s' % s
            if key in ["GD", "RD", "OD"]:
                self.dacs[dackey] = int(biases[key] / self.convertbiases[key]) & 0xfff
                self.write(dacaddress, self.dacs[dackey] + (outputnum[key] << 12))
            elif key == "OG":
                dackeyshift = "OG_S" + '%s' % s
                if biases[key] > 0:
                    self.dacs[dackey] = int(biases[key] / self.convertbiases[key]) & 0xfff
                    self.dacs[dackeyshift] = 0
                else:
                    self.dacs[dackey] = 0
                    self.dacs[dackeyshift] = int(-biases[key] / self.convertbiases["OG_S"]) & 0xfff
                self.write(dacaddress, self.dacs[dackey] + (outputnum[key] << 12))
                self.write(dacaddress, self.dacs[dackeyshift] + (outputnum["OG_S"] << 12))
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

        # activates DAC outputs
        self.write(0x400101 + (s << 4), 1)

    def get_bias_voltages(self, s, readback=False):
        """
        In REB3, we can read from the slow ADC+mux or from the stored DAC values.
        :type s: int
        :type readback: bool
        :param s: stripe
        """
        self.check_location(s)
        orderkeys = self.groups['BIASES']
        dictvalues = {}
        dictcomments = {}

        for key in self.groups['BIASES']:
            if readback:
                adckey = key + '_%s' % s
                value = self.slow_adc_read(adckey)
                dictvalues[key] = value
                dictcomments[key] = '[V] %s read through slow ADC'  % key
            else:
                dackey = key + '%s' % s
                if key == 'OG':
                    dackeyshift = "OG_S" + '%s' % s
                    dictvalues[key] = round(self.dacs[dackey] * self.convertbiases[key] \
                                      - self.dacs[dackeyshift] * self.convertbiases["OG_S"], 3)
                else:
                    dictvalues[key] = round(self.dacs[dackey] * self.convertbiases[key], 3)
                dictcomments[key] = '[V] %s voltage setting' % key

        return MetaData(orderkeys, dictvalues, dictcomments)

    def check_location(self, s, loc=3):
        if s not in [0, 1, 2]:
            raise ValueError("Invalid REB stripe (%d)" % s)
        if loc not in [1, 2, 3]:
            raise ValueError("Invalid Location code (%d)" % loc)
        return True

   # ----------------------------------------------------------

    def init_slow_adc(self):
        """
        Initializes the slow ADC for monitoring if necessary.
        Values may need to be changed based on CCD type.
        :return:
        """
        if self.hardware == 'REB3':
            pass
        elif self.hardware == 'REB4':
            self.write(0x600101, 0x2060)
            self.write(0x600101, 0x2220)
            self.write(0x600101, 0x2420)

    def slow_adc_readmux(self, muxtuple):
        """
        Triggers reading of slow ADC pointed at the given address
        For REB3, muxtuple is:
        extmux: address on external 8-channel mux
        adcmux: address on internal 16-channel mux
        For REB4:
        muxsam: top-level mux selection
        muxselect: low-level mux selection
        adcmux: internal 4-channel mux of the ADC
        :rtype: int
        """

        if self.hardware == 'REB3':
            extmux, adcmux = muxtuple
            # includes enable bit on 8-channel mux
            self.write(0x600101, ((extmux & 7) << 5) + (1 << 4) + (adcmux & 0xf))
            raw = self.read(0x601010, 1)[0x601010]
            value = raw & 0xfff
            checkextmux = (raw >> 21) & 7
            checkadcmux = (raw >> 12) & 0xf
            if (checkextmux != extmux) or (checkadcmux != adcmux):
                print('Warning: mismatch in slow ADC read %d, %d' % (checkextmux, checkadcmux))
            # convert ADU to V or mA (for current sources)
            value *=  self.adcconvert

        elif self.hardware == 'REB4':
            # TODO: initialization needs to be done elsewhere
            # assuming range does not need to be changed for each value individually
            muxsam, muxselect, adcmux = muxtuple
            # write to muxes and ADC channel select
            self.write(0x600101, ((muxsam & 7) << 19) + ((muxselect & 7) << 16) + (1 << 8) + ((adcmux & 0x3) << 5))
            raw = self.read(0x601010, 1)[0x601010]
            value = raw & 0xfff
            checkadcmux = (raw >> 13) & 0x3
            if checkadcmux != adcmux:
                print('Warning: mismatch in slow ADC, reading channel %d' %  checkadcmux)
            # convert ADU to V or mA (for current sources)
            value *=  self.adcconvert[adcmux]

        else:
            raise ValueError('No slow ADC rules for this hardware type: %s' % self.hardware)

        return value

    def aspic_temperature_read(self):
        """
        Reads all the ASPIC temperature sensors.
        Not changed between REB3 and REB4.
        :return: MetaData
        """
        self.write(0x600100, 1)

        #time.sleep(0.01)

        temps = self.read(0x601000, 6)
        orderkeys = ['T_ASPT_0', 'T_ASPB_0', 'T_ASPT_1', 'T_ASPB_1', 'T_ASPT_2', 'T_ASPB_2']
        dictvalues = {}
        dictcomments = {}

        for iaddress, key in enumerate(orderkeys):
            dictvalues[key] = temps[0x601000 + iaddress] * self.adcconvert
            dictcomments[key] = '[V] ASPIC temperature sensor %s' % key
            # TODO: conversion to temperature

        return MetaData(orderkeys, dictvalues, dictcomments)

    def slow_adc_read(self, param):
        """
        Reads any parameter by name.
        :type param: string
        :rtype: float
        """
        muxtuple = self.adcmap[param]

        value = self.slow_adc_readmux(muxtuple)
        # resistor bridge for biases
        if param[:2] in self.groups['BIASES']:
            value *= 11

        return value

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

        # sort dictionary keys for reliable order in the header
        for key in sorted(self.adcmap.keys()):
            # last digit of parameter name is always the stripe
            if key[-1] == '%d' % s:
                value = self.slow_adc_read(key)
                orderkeys.append(key)
                dictvalues[key] = round(value, 3)
                if key[:2] == 'CS':
                    dictcomments[key] = '[mA] current in source %s' % key
                else:
                    dictcomments[key] = '[V] %s voltage read through slow ADC' % key

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

    def apply_aspic_config(self, aspic_dict, s=0, loc=3):
        """
        Apply settings from dict to the ASPIC(s) designed by the stripe s (amongst 0,1,2) and the location
        (1 for bottom, 2 for top, 3 for both).
        """
        self.check_location(s, loc)

        if loc == 1 or loc == 3:
            # bottom ASPIC
            self.aspics['bottom'][s].set_aspic_fromdict(aspic_dict)
            AspicData = self.aspics['bottom'][s].write_all_registers()
            for address in range(2):
                self.write_spi(0xB00000, s, 1, AspicData[address], True)
        if loc == 2 or loc == 3:
            # top ASPIC
            self.aspics['top'][s].set_aspic_fromdict(aspic_dict)
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
    # ----------------------------------------------------------

    def get_fpga_config(self, s):  # stripe 's'
        """
        Output for header.
        """
        #TODO: check readback versus stored values for biases, then remove/keep(?) stored values
        config = FPGA.get_fpga_config(self, s)
        config.update(self.get_clock_voltages())
        config.update(self.get_bias_voltages(s, readback=False))
        config.update(self.get_current_source(s, readback=False)) # readback with slow ADC
        config.update(self.slow_adc_stripe(s))
        config.update(self.get_aspic_config(s, check=False))

        return config

