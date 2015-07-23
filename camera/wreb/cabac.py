#! /usr/bin/env python
#
# LSST
# Python minimal interface for the CABAC1 chip
#
# Laurent Le Guillou - Claire Juramy

from lsst.camera.generic import bidi


## -----------------------------------------------------------------------

def parse_reg_clock(reg):
    """
        Parses CABAC 16-bit data two 8-bit clock currents
    """

    cfall = (reg >> 8) & 0xff
    crise =  reg & 0xff

    return crise, cfall

## -----------------------------------------------------------------------

def parse_reg_dc(reg):
    """
        Parses CABAC 16-bit register into 10-bit DAC setting
    """

    dac=  reg & 0x3ff

    return dac

## -----------------------------------------------------------------------

class CABAC(object):
    """
    CABAC settings
    """
    ODconv = 0.049 #V/DAC unit conversion (approximation)
    # beware of CABAC2 offsets
    GDconv = 0.049
    RDconv = 0.049
    OGconv = 0.049
    # set of parameters that CABAC() keeps track of
    params = ['ODEM', 'ODRM',"OD0EM", "OD1EM","OD0RM", "OD1RM",
              "GD", "RD", "OG", "SPA", 
              "P0R", "P1R", "P2R", "P3R", "S0R", "S1R", "S2R", 'RGR',
              "P0F", "P1F", "P2F", "P3F", "S0F", "S1F", "S2F", 'RGF',
              "HIZ", "SAFE", "PULS", "MUX", "OFMUX", "EXPCK"]
    # define groups for programming shortcuts
    groups = {'OD': ["OD0EM", "OD0RM", "OD1EM", "OD1RM"],
              'OD0': ["OD0EM", "OD0RM"],
              'OD1': ["OD1EM", "OD1RM"],
              'ODEM': ['OD0EM', 'OD1EM'],
              'ODRM': ['OD0RM', 'OD1RM'],
              'IP': ["P0R", "P1R", "P2R", "P3R", "P0F", "P1F", "P2F", "P3F"],
              'IPR': ["P0R", "P1R", "P2R", "P3R"],
              'IPF': ["P0F", "P1F", "P2F", "P3F"],
              'IS': ["S0R", "S1R", "S2R", "S0F", "S1F", "S2F"],
              'ISR': ["S0R", "S1R", "S2R"],
              'ISF': ["S0F", "S1F", "S2F"],
              'IC': ["P0R", "P1R", "P2R", "P3R", "S0R", "S1R", "S2R", 'RGR',
                     "P0F", "P1F", "P2F", "P3F", "S0F", "S1F", "S2F", 'RGF'],
              'ICR': ["P0R", "P1R", "P2R", "P3R", "S0R", "S1R", "S2R", 'RGR'],
              'ICF': ["P0F", "P1F", "P2F", "P3F", "S0F", "S1F", "S2F", 'RGF']}

    conv = {'OD0EM': ODconv,
            'OD1EM': ODconv,
            'OD0RM': ODconv,
            'OD1RM': ODconv,
            'OD0': ODconv,
            'OD1': ODconv,
            'OD': ODconv,
            'GD': GDconv,
            'RD': RDconv,
            'OG': OGconv,
            'SPA': GDconv}
    SPIaddress = bidi.BidiMap([],[])
    SPIaddress.update({"OD0EM": 8, "OD0RM": 9, "OD1EM": 10, "OD1RM": 11, "RD": 12, "GD": 13, "OG": 14, "SPA": 15,
        "P0": 0, "P1": 1, "P2": 2, "P3": 3, "S0": 4, "S1": 5, "S2": 6, "RG": 7,
        "MUX": 16, "OFMUX": 17, "EXPCK": 18, "HIZ": 19, "SAFE": 20, "PULS": 21})
    # Mux maps: see function for use due to complications
    mux0map = bidi.BidiMap(["TEMP", "SPA", "OG", "GD", "RD", "OD0", "OD1"], range(1, 8))
    mux0map.update({"ATIME": 15})
    mux1map = bidi.BidiMap(["EXT0", "EXT1"], [6, 7])
    clockmap = bidi.BidiMap(["P0", "P1", "P2", "P3", "S0", "S1", "S2", "RG"], range(8, 16))

    def __init__(self):
        self.settings = {}
        for param in self.params:
            self.settings[param] = 0
        self.settings["SAFE"] = 1
        self.settings["EXPCK"] = 0xff
        # actual CABAC1/2 settings at start-up
    
# Note: serial link works differently from CABAC0. Setting a parameter
# returns a list of registers to write (address on CABAC + value).
    def spi_reg(self, param, value):
        """
        Elementary register building, no test included.
        :param param: string
        :param value: integer
        :return: integer
        """
        return (self.SPIaddress[param] << 16) + value

    def set_cabac_fromstring(self, param, value):
        """
        Saves new value to object and returns registers to write to the SPI link.
        :param param: string
        :param value: voltage for biases, integer for the rest, tuple of strings for mux
        :return: list
        """
        regs = []
        value_int = 0

        if param in self.groups:
            for subparam in self.groups[param]:
                regs.extend(self.set_cabac_fromstring(subparam, value))
        else:
            if param in self.conv:
                value_int = int(value // self.conv[param]) & 0x3ff
                regs.append(self.spi_reg(param, value_int))
            elif param in self.groups['IC']:
                value_int = value & 0xff
                ck, side = param[:-1], param[-1]
                if side == 'R':
                    ifall = self.settings[ck + 'F']
                    irise = value_int
                else :
                    irise = self.settings[ck + 'R']
                    ifall = value_int
                regs.append(self.spi_reg(ck, (ifall << 8) + irise))
            elif param == "PULS":
                value_int = value & 1
                regs.append(self.spi_reg(param, value_int))
            elif param == "MUX":
                # need two strings as parameters for mux outputs
                value_int = self.set_muxout(value[0], value[1])
                regs.append(self.spi_reg(param, value_int))
            elif param == "OFMUX":
                value_int = value & 0xff
                regs.append(self.spi_reg(param, value_int * 0x101))
            elif param == "EXPCK":
                value_int = value & 0xff
                regs.append(self.spi_reg(param, value_int))
            else:
                raise ValueError("No CABAC parameter with this name: "+ param)
            self.settings[param] = value_int
            
        return regs

    def get_cabac_fromstring(self, param):

        if param not in self.params:
            raise ValueError("No CABAC parameter with this name: "+ param)

        value = self.settings[param]

        return value

    # ----------------------------------------------------------

    def set_from_register(self, address, reg, check=True):
        """
        Takes result from CABAC readback and updates the object.
        If check is True, also checks against the stored value.
        :param address: int
        :param reg: int
        :param check: bool
        """
        name = self.SPIaddress.reverse[address]

        if address < self.SPIaddress["OD0EM"]:
            savedr = self.settings[name + 'R']
            savedf = self.settings[name + 'F']
            crise, cfall = parse_reg_clock(reg)
            self.settings[name + 'R'] = crise
            self.settings[name + 'F'] = cfall
            if check:
                if savedr != crise or savedf != cfall:
                    print("Warning: unexpected values for %s: %d, %d" % (name, crise, cfall))
        else:
            saved = self.settings[name]
            if address < self.SPIaddress["MUX"]:
                value_int = parse_reg_dc(reg)
            else:
                value_int = reg & 0xFFFF
            self.settings[name] = value_int
            if check:
                if saved != value_int:
                    print("Warning: unexpected value for %s: %d" % (name, value_int))

    def read_all_registers(self, regs, check=True):
        """
        Takes values of registers from readback and updates the object. If 'check' is True, checks against previous
        values.
        Note that this should be applied to the right CABAC object(s).
        :param regs: dict
        :param check: bool
        """
        # Now accepts any number of parameters in the dict
        #if len(regs) < 22:
        #    print("Error: need 22 registers for complete readback.")

        for add, reg in regs.iteritems():
            if add > -1 and add < 22:
                self.set_from_register(add, reg, check)
            else:
                print("Warning: unknown address for CABAC1 register: %d" % add)

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
    def set_muxout(self, output0, output1="None"):
        """
        Multiplexer management, takes in names of what we want on each mux output.
        There are some quirks due to CABAC1 mux addressing bug.
        Passing unknown parameters to both outputs disables both muxes.
        :param output0: string
        :param output1: string
        :return:
        """
        ena0 = 0
        ena1 = 0
        add0 = 0
        add1 = 0

        if self.mux0map.has_key(output0):
            ena0 = 1
            add0 = self.mux0map[output0]
            if output1:
                if self.mux1map.has_key(output1):
                    add1 = self.mux1map[output1]
                    ena1 = 1
                else:
                    print("Incompatible setting for multiplexers: %s, %s" % (output0, output1))
        elif self.clockmap.has_key(output0):
            ena0 = 1
            ena1 = 1  # inverted mux blocks, need to enable both
            add1 = self.clockmap[output0]
            if output1:
                if self.clockmap.has_key(output1) and output1 != "RG":
                    add0 = self.clockmap[output1]
                else:
                    print("Incompatible setting for multiplexers: %s, %s" % (output0, output1))
                    add0 = 8
        else:
            # print("Unknown parameter for MuxOut0: %s" % output0)
            if self.mux1map.has_key(output1):
                ena1 = 1
                add1 = self.mux1map[output1]
            elif self.clockmap.has_key(output1) and output1 != "RG":
                ena0 = 1
                ena1 = 1
                add0 = self.clockmap[output1]
                add1 = 8
            #else:
                # print("Unknown parameter for MuxOut1: %s" % output0)

        reg = (ena1 << 9) | (ena0 << 8) | (add1 << 4) | add0

        return reg

    # ----------------------------------------------------------

    def check_bias_safety(self, param, value):
        """
        Checks that the given parameter is safe for the CCD, comparing to saved values.
        :param param: string
        :param value: float
        :return: bool
        """
        # safety: OG<OD
        if param == "OG":
            for subparam in self.groups['OD']:
                if (self.settings[subparam]*self.conv[subparam]) < value:
                    print("Warning: trying to program OG at %f, higher than %s" % (value, subparam))
                    return False

        # safety: OD-RD < 20 V, but preferably also OD>RD
        elif param in self.groups['OD']:
            if value < self.settings['RD']*self.conv['RD']:
                print("Warning: trying to program %s lower than RD" % param)
                return False
            elif value > self.settings['RD']*self.conv['RD'] + 20:
                print("Warning: trying to program %s higher than RD + 20 V" % param)
                return False
        elif param == "RD":
            for subparam in self.groups['OD']:
                if self.settings[subparam]*self.conv[subparam] < value:
                    print("Warning: trying to program RD higher than %s" % subparam)
                    return False
                elif self.settings[subparam]*self.conv[subparam] > value + 20:
                    print("Warning: trying to program RD lower than %s - 20 V" % subparam)
                    return False

        return True

    # ----------------------------------------------------------

    def get_header(self, position = ''):
        """
        Writes current CABAC settings to a dictionary to include in FITS header file.
        :param position: string = 'T' or 'B' plus stripe information, or nothing
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
            if field in self.conv:
                header[key] = self.settings[field] * self.conv[field]
            else:
                header[key] = self.settings[field]
            keys.append(key)
            comments[key] = 'CABAC2 '+ field + positioncomment

        return keys, header, comments

