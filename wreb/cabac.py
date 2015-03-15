#! /usr/bin/env python
#
# LSST
# Python minimal interface for the CABAC1 chip
#
# Laurent Le Guillou - Claire Juramy

## -----------------------------------------------------------------------

def parse_reg_clock(reg):
    """
        Parses CABAC 32-bit register into address and two 8-bit clock currents
    """

    add = (reg >> 16)  & 0xff
    crise = (reg >> 8) & 0xff
    cfall =  reg & 0xff
    #TODO: check rise/fall order

    return add, crise, cfall

## -----------------------------------------------------------------------

def parse_reg_dc(reg):
    """
        Parses CABAC 32-bit register into address and 10-bit DAC setting
    """

    add = (reg >> 16)  & 0xff
    dac=  reg & 0x3ff

    return add, dac

## -----------------------------------------------------------------------

class CABAC(object):
    """
    CABAC settings
    """
    ODconv = 0.049 #V/DAC unit conversion (approximation)
    # beware of CABAC1 offsets
    GDconv = 0.049
    RDconv = 0.049
    OGconv = 0.049
    params = ["OD", "OD0", "OD1", "GD", "RD", "OG", "IP", "IS", "IRG", "IC", "SPA",
              "P0", "P1", "P2", "P3", "S0", "S1", "S2", "RG"]  # list of accepted parameters
    settings = {}
    conv = {'OD0': ODconv,
            'OD1': ODconv, 
            'GD': GDconv, 
            'RD': RDconv,
            'OG': OGconv,
            'SPA': GDconv}
    SPIaddress = {"OD0EM": 8, "OD0RM": 9, "OD1EM": 10, "OD1RM": 11, "RD": 12, "GD": 13, "OG": 14, "SPA": 15,
        "P0": 0, "P1": 1, "P2": 2, "P3": 3, "S0": 4, "S1": 5, "S2": 6, "RG": 7,
        "MUX": 16, "OFMUX": 17, "EXPCLK": 18, "HIZ": 19, "SAFE": 20, "PULS": 21}

    def __init__(self):
        for param in self.params:
            self.settings[param] = 0
    
    
# Note: serial link works differently from CABAC0. Setting a parameter
# returns a list of registers to write (address on CABAC + value).
    def spi_reg(self, param, value):
        """
        Elementary register building, no test included.
        :param param: string
        :param value: integer
        :return: integer
        """
        return self.SPIaddress[param] << 16 + value

    def set_cabac_fromstring(self, param, value):
        """
        Saves new value to object and returns registers to write to the SPI link.
        :param param: string
        :param value: voltage for biases, integer for the rest
        :return: list
        """
        regs = []
        value_int = 0
        if param not in self.params:
            raise ValueError("No CABAC parameter with this name: "+ param)

        if param == "OD":
            regs = self.set_cabac_fromstring("OD0", value)
            regs.extend(self.set_cabac_fromstring("OD1", value))
        elif param == "OD0":
            value_int = int(value // self.conv[param]) & 0x3ff
            regs.append(self.spi_reg("OD0EM", value_int))
            regs.append(self.spi_reg("OD0RM", value_int))
        elif param == "OD1":
            value_int = int(value // self.conv[param]) & 0x3ff
            regs.append(self.spi_reg("OD1EM", value_int))
            regs.append(self.spi_reg("OD1RM", value_int))
        elif param in ["GD", "RD", "OG", "SPA"]:
            value_int = int(value // self.conv[param]) & 0x3ff
            regs.append(self.spi_reg(param, value_int))
        elif param in ["P0", "P1", "P2", "P3", "S0", "S1", "S2", "RG"]:
            value_int = value & 0xff
            # rise and fall currents
            regs.append(self.spi_reg(param, value_int)* 0x101)
        elif param == "IP":
            value_int = value & 0xff
            for subpar in ["P0", "P1", "P2", "P3"]:
                regs.extend(self.set_cabac_fromstring(subpar, value))
        elif param == "IS":
            value_int = value & 0xff
            for subpar in ["S0", "S1", "S2"]:
                regs.extend(self.set_cabac_fromstring(subpar, value))
        elif param == "IC":
            regs = self.set_cabac_fromstring("IP", value)
            regs.extend(self.set_cabac_fromstring("IS", value))
            regs.extend(self.set_cabac_fromstring("RG", value))

        self.settings[param] = value_int
        return regs

    def get_cabac_fromstring(self, param):

        if param not in self.params:
            raise ValueError("No CABAC parameter with this name: "+ param)

        value = self.settings[param]

        return value

    # ----------------------------------------------------------

    def set_from_register(self, reg, check=True):
        """
        Takes result from CABAC readback and updates the object.
        If check is True, then checks against the stored value.
        """
        
        #splits register
        data = reg & 0xFFFF
        address = (reg >> 16)  & 0x3f

        #TODO: find dict key from content in SPIaddress

    def read_all_registers(self, regs, check=True):
        """
        Takes values of registers from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right CABAC object(s).
        """
        if len(regs) < 22:
            print("Error: need 22 registers for complete readback.")

        else:
            for reg in regs:
                self.set_from_register(reg, check)


    # ----------------------------------------------------------

    def get_header(self, position = ''):#string 'T' or 'B' or nothing
        """
        Writes current CABAC settings to a dictionary to include in FITS header file
        """

        header = {}

        suffix = ""
        if position != '':
            suffix = "_" + position

        for field in ['OD0', 'OD1', 'GD', 'RD', 'OG']:
            key = "V_" + field + suffix
            header[key] = self.settings[field] * self.conv[field]

        header["I_P" + suffix]  = self.settings["IP"]
        header["I_S" + suffix]  = self.settings["IS"]
        header["I_RG" + suffix] = self.settings["RG"]

        return header

