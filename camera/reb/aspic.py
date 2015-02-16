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
            raise ValueError("Erroneous gain value for ASPIC")

    def write_all_registers(self):
        """
        Takes values in the object and writes them in register format.
        Note that the register needs to be completed with the addressing bits to target the right ASPIC(s).
        """
        regs = {}

        regs[0] = self.Gain << 4 + self.RC
        regs[1] = self.Clamps
        regs[2] = self.AF1 << 1 + self.TM

        return regs




