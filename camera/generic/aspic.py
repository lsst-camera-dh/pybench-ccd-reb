#! /usr/bin/env python
#
# LSST / LPNHE
# Python minimal interface for the ASPIC chip
#
# Current version ASPIC3 chip with DREB1 interface

## -----------------------------------------------------------------------
__author__ = 'juramy'

class ASPIC(object):
    """
    ASPIC settings
    """
    params = ["GAIN", "RC", "AF1", "TM", "CLS"]  # list of accepted parameters
    # could be cleaned up with bidi for addressing like CABAC1

    def __init__(self):
        self.Gain = 0
        self.RC = 0
        self.TM = True
        self.AF1 = True
        self.Clamps = 0

    def set_gain(self, g):
        """
        Changes gain setting, defined as an integer between 0 and 15.
        Returns the register value to write.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        :param g: int
        :return: int
        """
        if g>=-0.1 and g<=15.1:
            self.Gain = int(g)
        else:
            raise ValueError("Erroneous gain value for ASPIC")
        return (self.Gain << 4) + self.RC

    def set_RC(self, rc):
        """
        Changes RC constant setting, defined as an integer between 0 and 15.
        Returns the register value to write.
        :param rc: int
        :return: int
        """
        if rc>=-0.1 and rc<=15.1:
            self.RC = int(rc)
        else:
            raise ValueError("Erroneous RC value for ASPIC")
        return (self.Gain << 4) + self.RC

    def set_TM(self, tm):
        """
        Sets the Transparent Mode to true or false. Returns the register value to write.
        :param tm: bool
        :return: int
        """
        self.TM = tm
        code = 0
        if self.TM:
            code += 1
        if self.AF1:
            code += 2
        return 1<<17 | code

    def set_AF1(self, af1):
        """
        Sets the Amplifier Forced to 1 mode to true or false. Returns the register value to write.
        :param af1: bool
        :return: int
        """
        self.AF1 = af1
        code = 0
        if self.TM:
            code += 1
        if self.AF1:
            code += 2
        return 1<<17 | code

    def clamp_channel(self, c):
        """
        Puts a permanent clamp on the given channel (0 to 7). Returns the register value to write with current
        clamped channels.
        :param c: int
        :return:
        """
        if c>=-0.1 and c<=7.1:
            self.Clamps += 1 << int(c)
        else:
            raise ValueError("Erroneous clamp channel for ASPIC")
        return 1<<16 | self.Clamps

    def clamp_all(self, clamping = True):
        """
        Clamps or unclamps all channels at once, depending of the value of the 'clamping' parameter.
        Returns the register value to write.
        :param clamping: bool
        :return: int
        """
        if clamping:
            self.Clamps = 0xFF
        else:
            self.Clamps = 0
        return 1<<16 | self.Clamps

    def set_aspic_fromstring(self, param, value):
        """
        Sets any ASPIC parameter as given by param.
        :param param: string
        :param value:
        :return:
        """
        reg = 0
        if param == "GAIN":
            reg = self.set_gain(value)
        elif param == "RC":
            reg = self.set_RC(value)
        elif param == "CLS":
            self.Clamps = value & 0xFF
            reg = 1<<16 | self.Clamps
        elif param == "TM":
            reg = self.set_TM(value)
        elif param == "AF1":
            reg = self.set_AF1(value)
        else :
            raise ValueError("No ASPIC parameter with this name: "+ param)
        return reg

    def set_aspic_fromdict(self, aspic_dict):
        """
        Configure fully ASPIC from bcf-style dictionary.
        Use write_all_registers afterwards to get the registers.
        :param aspic_dict:
        :return:
        """
        self.Gain = aspic_dict['gain']
        self.RC = aspic_dict['rc']
        self.TM = aspic_dict['transparent_mode']
        self.AF1 = aspic_dict['af']
        self.Clamps = aspic_dict['clamp']

    def write_all_registers(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        regs = [0,0,0]

        regs[0] = self.Gain << 4 | self.RC
        regs[1] = 1<<16 | self.Clamps
        regs[2] = self.set_TM(self.TM)

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
        :param regs: dict
        :param check: bool
        """
        # Now accepts any number of registers (in a dictionary).
        #if len(regs) < 3:
        #    print("Error: need three registers for complete readback.")

        for add,reg in regs.iteritems():
            if add == 0:
                self.read_gain_rc(reg, check)
            elif add == 1:
                self.read_clamps(reg, check)
            elif add == 2:
                self.read_modes(reg, check)
            else:
                print("Warning: unknown register in ASPIC readback.")

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
        keys = []
        header = {}
        comments = {}

        if position:
            suffix = "_" + position
            positioncomment = ' at ' + position
        else:
            suffix = ''
            positioncomment = ''

        for field in self.params:
            key = field + suffix
            keys.append(key)
            header[key] = self.get_aspic_fromstring(field)
            comments[key] = 'ASPIC '+ field + positioncomment

        return keys, header, comments


