#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
#
# This one is for REB1 with DREB1. This means CABAC0, ASPIC2 (not managed by the FPGA),
# and first version of the sequencer (with no pointers).
# Take from wreb for more advanced REBs and DREBs.

from lsst.camera.generic.fpga import *

import cabac0 as cabac


class FPGA0(FPGA):
    # ctrl_host = "lpnws4122"
    # reb_id = 2

    serial_conv = 0.00306  # rough conversion for DACs, no guarantee
    parallel_conv = 0.00348

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2):
        FPGA.__init__(self, ctrl_host, reb_id)
        # declare two CABACs for each stripe even if they will not be used
        # (at least we will want to initialize to 0 if they exist)
        self.cabac_top = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.cabac_bottom = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.dacs = {"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0, "HEAT1": 0, "HEAT2": 0,
                     "I_OS": 0}
        # modify class Instruction so that it uses the right opcodes and bit shifts
        Instruction.OP_CallFunction = 0x1
        Instruction.OP_JumpToSubroutine = 0x2
        Instruction.OP_ReturnFromSubroutine = 0x3
        Instruction.OP_EndOfProgram = 0x4
        Instruction.OP_codes = bidi.BidiMap(Instruction.OP_names,
                                            [Instruction.OP_CallFunction,
                                             Instruction.OP_JumpToSubroutine,
                                             Instruction.OP_ReturnFromSubroutine,
                                             Instruction.OP_EndOfProgram])
        Instruction.SubAddressShift = 18

    # --------------------------------------------------------------------

    def increment(self):
        """
        Send the command to increment the ADC sampling time by 1 cycle after
        each ADC trigger.
        """
        self.write(0x330000, 1)

    def stop_increment(self):
        """
        Send the command to stop incrementing the ADC sampling time and reset the shift.
        """
        self.write(0x330000, 0)
        self.write(0x340000, 0)

    def increment_status(self):
        """
        Checks is the ADC incrementing is on.
        :return:
        """
        return bool(self.read(0x330000, 1)[0x330000])

    # ----------------------------------------------------------

    def set_clock_voltages(self, voltages):
        """
        Sets voltages as defined in the input dictionary, 
        keeps others as previously defined.
        """

        # values to be set in the register for each output
        outputnum = {"V_SL": 0, "V_SH": 1, "V_RGL": 2, "V_RGH": 3, "V_PL": 4, "V_PH": 5, "HEAT1": 6, "HEAT2": 7}

        for key in iter(voltages):
            if key in ["V_SL", "V_SH", "V_RGL", "V_RGH"]:
                self.dacs[key] = int(voltages[key] / self.serial_conv) & 0xfff
            elif key in ["V_PL", "V_PH"]:
                self.dacs[key] = int(voltages[key] / self.parallel_conv) & 0xfff
            elif key in ["HEAT1", "HEAT2"]:
                self.dacs[key] = int(voltages[key]) & 0xfff
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)

            self.write(0x400000, self.dacs[key] + (outputnum[key] << 12))

        # activates DAC outputs
        self.write(0x400001, 1)

    # ----------------------------------------------------------

    def get_clock_voltages(self):
        """
        No readback available, using values stored in fpga object.
        """
        fitsheader = {}
        for key in iter(self.dacs):
            if key in ["V_SL", "V_SH", "V_RGL", "V_RGH"]:
                # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.serial_conv)
                fitsheader[key] = self.dacs[key] * self.serial_conv
            elif key in ["V_PL", "V_PH"]:
                # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.parallel_conv)
                fitsheader[key] = self.dacs[key] * self.parallel_conv
            else:
                # fitsheader[key]= "{:d}".format(self.dacs[key])
                fitsheader[key] = self.dacs[key]

        return fitsheader

    # ----------------------------------------------------------

    def set_current_source(self, current, ccdnum=0):
        """
        Sets current source DAC value for given CCD (0, 1, 2).
        """

        key = "I_OS"

        self.dacs[key] = current & 0xfff

        self.write(0x400010, self.dacs[key] + (ccdnum << 12))

        # activates DAC output
        self.write(0x400011, 1)

    # ----------------------------------------------------------

    def get_current_source(self):
        """
        No readback available, using values stored in fpga object.
        """

        key = "I_OS"

        return {key: self.dacs[key]}

    # ----------------------------------------------------------

    def get_dacs(self):
        """
        All DACs settings into MetaData format.
        No readback available, using values stored in fpga object.
        :return: MetaData
        """
        keys = ["V_SL", "V_SH", "V_RGL", "V_RGH", "V_PL", "V_PH",
                "HEAT1", "HEAT2", "I_OS"]
        fitsheader = self.get_clock_voltages()

        comments = {
            'V_SL': 'Serial clocks low voltage',
            'V_SH': 'Serial clocks high voltage',
            'V_RGL': 'Reset Gate clock low voltage',
            'V_RGH': 'Reset Gate clock high voltage',
            'V_PL': 'Parallel clocks low voltage',
            'V_PH': 'Parallel clocks high voltage',
            'HEAT1': 'REB heater 1 setting',
            'HEAT2': 'REB heater 2 setting',
            'I_OS': 'Current sources setting'
        }

        return MetaData(keys, fitsheader, comments, 'REB DACS')

    # ----------------------------------------------------------

    def get_cabac_config(self, s):  # stripe 's'
        """
        read CABAC configuration for stripe <s>,
        store it in the CABAC objects and the header string.
        """
        check_location(s)

        self.write(0x500001, s)  # starts the CABAC config readout

        top_config = self.read(0x500110, 5)  # 0 - 4
        bottom_config = self.read(0x500120, 5)  # 0 - 4

        self.cabac_top[s].set_from_registers(top_config)
        self.cabac_bottom[s].set_from_registers(bottom_config)

        keyst, configt, comt = self.cabac_top[s].get_header("%dT" % s)
        keysb, configb, comb = self.cabac_bottom[s].get_header("%dB" % s)

        config = MetaData(keyst, configt, comt, 'CABACS')
        config.update_ordered(keysb, configb, comb)

        return config

    # ----------------------------------------------------------

    def send_cabac_config(self, s=0):  # stripe 's'
        """
        Writes the current CABAC objects of the given stripe to the FPGA registers
        """
        check_location(s)

        regs_top = self.cabac_top[s].write_to_registers()
        regs_bottom = self.cabac_bottom[s].write_to_registers()

        for regnum in range(0, 5):
            self.write(0x500010 + regnum, regs_top[regnum])
            self.write(0x500020 + regnum, regs_bottom[regnum])

        self.write(0x500000, s)  # starts the CABAC configuration

    # ----------------------------------------------------------

    def set_cabac_value(self, param, value, s=0):
        """
        Sets the CABAC parameter at the given value on both CABACs of the given stripe.
        Default value for retro-compatibility.
        """
        check_location(s)
        self.cabac_top[s].set_cabac_fromstring(param, value)
        self.cabac_bottom[s].set_cabac_fromstring(param, value)

    # ----------------------------------------------------------

    def check_cabac_value(self, param, value, s=0):
        """
        Gets the current value of the CABAC objects for the given parameter on the given stripe
        and checks that it is correct.
        """
        prgm = (self.cabac_top[s].get_cabac_fromstring(param) +
                self.cabac_bottom[s].get_cabac_fromstring(param))

        for prgmval in prgm:
            if abs(prgmval - value) > 0.2:
                raise StandardError(
                    "CABAC readback different from setting for %s: %f != %f" %
                    (param, prgmval, value))

    # ----------------------------------------------------------

    def reset_cabac(self, s=0):  # stripe 's'
        """
        Writes 0 to all the FPGA CABAC registers for stripe s
        """
        check_location(s)

        for regnum in range(0, 5):
            self.write(0x500010 + regnum, 0)
            self.write(0x500020 + regnum, 0)

        self.write(0x500000, s)  # starts the CABAC configuration

        # ASPIC stuff: not needed for REB1+ASPIC2. Take from wreb for REB2/WGREB+ASPIC3.
