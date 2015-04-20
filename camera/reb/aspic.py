#! /usr/bin/env python
#
# LSST / LPNHE
# Python minimal interface for the ASPIC chip
#
# Current ASPIC3 chip with DREB1 interface
#
# wreb has the tested version, TAKE THAT ONE NOT THIS ONE

## -----------------------------------------------------------------------
__author__ = 'juramy'

class ASPIC(object):
    """
    ASPIC settings
    """
    params = ["GAIN", "RC", "AF1", "TM", "CLS"]  # list of accepted parameters

    def __init__(self):
        self.Gain = 0b1000
        self.RC = 0b0000
        self.TM = True
        self.AF1 = False
        self.Clamps = 0b0

    def set_gain(self, g):
        """
        Changes gain setting, defined as an integer between 0 and 15.
        :param g:
        :return:
        """
        if g>=0 and g<=15.1:
            self.Gain = int(g)
        else:
            raise ValueError("Erroneous gain value for ASPIC")

    def set_RC(self, rc):
        """
        Changes RC constant setting, defined as an integer between 0 and 15.
        :param g:
        :return:
        """
        if g>=0 and g<=15.1:
            self.RC = int(rc)
        else:
            raise ValueError("Erroneous RC value for ASPIC")

    def set_TM(self, tm):
        """
        Sets the Transparent Mode to true or false.
        :param tm:
        :return:
        """
        self.TM = tm

    def set_AF1(self, af1):
        """
        Sets the Transparent Mode to true or false.
        :param tm:
        :return:
        """
        self.AF1 = af1

    def clamp_channel(self, c):
        """
        Puts a permanent clamp on the given channel (0 to 7).
        :param c:
        :return:
        """
        if c>=0 and c<=7.1:
            self.Clamps += 1 << int(c)
        else:
            raise ValueError("Erroneous clamp channel for ASPIC")

    def set_aspic_fromstring(self, param, value):
        """
        Sets any ASPIC parameter as given by param.
        :param param:
        :param value:
        :return:
        """
        if param == "GAIN":
            self.set_gain(value)
        elif param == "RC":
            self.set_RC(value)
        elif param == "CLS":
            self.Clamps = value & 0xFF
        elif param == "TM":
            self.set_TM(value)
        elif param == "AF1":
            self.set_AF1(value)
        else :
            raise ValueError("No ASPIC parameter with this name: "+ param)

    def write_gain_rc(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        return (self.Gain << 4) + self.RC

    def write_clamps(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        return self.write_clamps()

    def write_modes(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        return (self.AF1 << 1) + self.TM


    def write_all_registers(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        regs = []

        regs[0] = self.write_gain_rc()
        regs[1] = self.write_clamps()
        regs[2] = self.write_modes()

        return regs

    def read_gain_rc(self, reg, check=True):
        """
        Takes values of register from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right ASPIC object(s).
        """
        ExpectedGain = self.Gain
        ExpectedRC = self.RC
        self.RC = reg & 0xF
        self.Gain = (reg >> 4) & 0xF
        if check:
            if ExpectedGain != self.Gain:
                print("Warning: unexpected value for Gain readback: %d" % self.Gain)
            if ExpectedRC != self.RC:
                print("Warning: unexpected value for RC readback: %d" % self.RC)

    def read_clamps(self, reg, check=True):
        """
        Takes values of register from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right ASPIC object(s).
        """
        Expected = self.Clamps

        self.Clamps = reg & 0xFF

        if check:
            if Expected != self.Clamps:
                print("Warning: unexpected value for clamps readback: %d" % self.Clamps)


    def read_modes(self, reg, check=True):
        """
        Takes values of register from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right ASPIC object(s).
        """
        ExpectedAF1 = self.AF1
        ExpectedTM = self.TM
        self.TM = reg & 0x1
        self.AF1 = (reg >> 1) & 0x1
        if check:
            if ExpectedAF1 != self.AF1:
                print("Warning: unexpected value for AF1 readback: %d" % self.AF1)
            if ExpectedTM != self.TM:
                print("Warning: unexpected value for TM readback: %d" % self.TM)

    def read_all_registers(self, regs, check=True):
        """
        Takes values of registers from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right ASPIC object(s).
        """
        if len(regs) < 3:
            print("Error: need three registers for complete readback.")

        else:
            self.read_gain_rc(regs[0], check)
            self.read_clamps(regs[1], check)
            self.read_modes(regs[2], check)

    def get_aspic_fromstring(self, param):
        """
        Reads any ASPIC parameter as given by param.
        :param param:
        :return:
        """
        if param == "GAIN":
            return self.Gain
        elif param == "RC":
            return self.RC
        elif param == "CLS":
            return self.Clamps
        elif param == "TM":
            return self.TM
        elif param == "AF1":
            return self.AF1
        else :
            raise ValueError("No ASPIC parameter with this name: "+ param)

    def get_header(self, position = ''):
        """
        Writes current ASPIC settings to a dictionary to include in FITS header file.
        'position' is a string to indicate top or bottom and/or stripe.
        """

        header = {}

        suffix = ""
        if position != '':
            suffix = "_" + position

        for field in ['GAIN', 'RC', 'CLS', 'TM', 'AF1']:
            key = field + suffix
            header[key] = self.get_aspic_fromstring(field)

        return header


