#! /usr/bin/env python
#
# LSST
# Python minimal interface for the CABAC1 chip
#
# Laurent Le Guillou - Claire Juramy

import bidi

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
    params = set(["OD", "OD0", "OD1", "OD0EM", "OD1EM","OD0RM", "OD1RM","GD", "RD", "OG", "IP", "IS", "IRG", "IC", "SPA",
              "P0", "P1", "P2", "P3", "S0", "S1", "S2", "RG", "HIZ", "SAFE", "PULS"])  # set of accepted parameters
    settings = {}
    conv = {'OD0': ODconv,
            'OD1': ODconv, 
            'GD': GDconv, 
            'RD': RDconv,
            'OG': OGconv,
            'SPA': GDconv}
    SPIaddress = bidi.BidiMap([],[])
    SPIaddress.update({"OD0EM": 8, "OD0RM": 9, "OD1EM": 10, "OD1RM": 11, "RD": 12, "GD": 13, "OG": 14, "SPA": 15,
        "P0": 0, "P1": 1, "P2": 2, "P3": 3, "S0": 4, "S1": 5, "S2": 6, "RG": 7,
        "MUX": 16, "OFMUX": 17, "EXPCLK": 18, "HIZ": 19, "SAFE": 20, "PULS": 21})
    # Mux maps: see function for use due to complications
    mux0map = bidi.BidiMap(["TEMP", "SPA", "OG", "GD", "RD", "OD0", "OD1"], range(1,8))
    mux0map.update({"ATIME": 15})
    mux1map = bidi.BidiMap(["EXT0", "EXT1"], [6, 7])
    clockmap = bidi.BidiMap(["P0", "P1", "P2", "P3", "S0", "S1", "S2", "RG"], range(8,16))

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
            regs = self.set_cabac_fromstring("OD0EM", value)
            regs.extend(self.set_cabac_fromstring("OD0RM", value))
        elif param == "OD1":
            regs = self.set_cabac_fromstring("OD1EM", value)
            regs.extend(self.set_cabac_fromstring("OD1RM", value))
        elif param in ["GD", "RD", "OG", "SPA", "OD0EM", "OD0RM", "OD1EM", "OD1RM"]:
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
        elif param == "PULS":
            value_int = value & 1
            regs.append(self.spi_reg(param, value_int))

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
        If check is True, also checks against the stored value.
        """
        
        #need address to find type of data
        address = (reg >> 16)  & 0x3f

        name = self.SPIaddress.reverse[address]
        saved = self.settings[name]

        if address < self.SPIaddress["OD0EM"]:
            value_int = parse_reg_clock(reg)[1]
        elif address < self.SPIaddress["MUX"]:
            value_int = parse_reg_dc(reg)
        else:
            value_int = reg & 0xFFFF
        self.settings[name] = value_int

        if check:
            if saved != value_int:
                print("Warning: unexpected value for %s: %d" % (name, data))

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
    def safety_off(self):
        """
        Specific to CABAC1: neutralizes all safety features. To be done when powering up CABAC1.
        """
        regs = [self.spi_reg("HIZ", 0b111111), self.spi_reg("SAFE", 0)]
        self.settings["HIZ"] = 0b111111
        self.settings["SAFE"] = 0

        return regs


    # ----------------------------------------------------------
    def set_muxout(self, output0, output1=None):
        """
        Multiplexer management, takes in names of what we want on each mux output.
        There are some quirks due to CABAC1 mux addressing bug.
        Passing None, None as parameters disables both muxes.
        :param output0: string
        :param output1: string
        :return:
        """
        ena0 = 0
        ena1 = 0
        add0 = 0
        add1 = 0

        if output0:
            ena0 = 1
            if self.mux0map.has_key(output0):
                add0 = self.mux0map[output0]
                if output1:
                    if self.mux1map.has_key(output1):
                        add1 = self.mux1map[output1]
                        ena1 = 1
                    else:
                        print("Incompatible setting for multiplexers: %s, %s" % (output0, output1))
            elif self.clockmap.has_key(output0):
                ena1 = 1  # inverted mux blocks
                add1 = self.clockmap[output0]
                if output1:
                    if self.clockmap.has_key(output1) and output1 != "RG":
                        add0 = self.clockmap[output1]
                    else:
                        print("Incompatible setting for multiplexers: %s, %s" % (output0, output1))
                        add0 = 8
            else:
                print("Unknown parameter for MuxOut0: %s" % output0)
        elif output1:
            ena1 = 1
            if self.mux1map.has_key(output1):
                add1 = self.mux1map[output1]
            elif self.clockmap.has_key(output1) and output1 != "RG":
                add0 = self.clockmap[output1]
                ena0 = 1
                add1 = 8
            else:
                print("Unknown parameter for MuxOut1: %s" % output0)

        reg = ena1 << 9 + ena0 << 8 + add1 << 4 + add0

        return reg

    # ----------------------------------------------------------

    def get_header(self, position = ''):
        """
        Writes current CABAC settings to a dictionary to include in FITS header file.
        :param position: string = 'T' or 'B' plus stripe information, or nothing
        """

        header = {}

        suffix = ""
        if position != '':
            suffix = "_" + position

        for field in self.params:
            if field in ['OD0', 'OD1', 'GD', 'RD', 'OG']:
                key = "V_" + field + suffix
                header[key] = self.settings[field] * self.conv[field]
            else:
                key = field + suffix
                header[key] = self.settings[field]

        return header

