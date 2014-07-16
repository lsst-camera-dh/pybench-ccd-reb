#! /usr/bin/env python
#
# LSST
# Python minimal interface for the CABAC chip
#
#

## -----------------------------------------------------------------------

def parse_reg_cabac(reg):
    """
        Parses CABAC 32-bit register into four 8-bit integers
    """

    int1 = reg & 0xff
    int2 = (reg >> 8) & 0xff
    int3 = (reg >> 16) & 0xff
    int4 = (reg >> 24) & 0xff

    return int1,int2,int3,int4

## -----------------------------------------------------------------------


class CABAC(object):
    """
    CABAC settings
    """
    ODconv = 0.1522 #V/DAC unit conversion (approximation)
    GDconv = 0.1412
    RDconv = 0.1414
    OGconv = 0.01895

    conv = {'OD0': ODconv, 
            'OD1': ODconv, 
            'GD': GDconv, 
            'RD': RDconv,
            'OG': OGconv}

    def __init__(self):
        self.OD0 = 0
        self.OD1 = 0
        self.I_parallel = 0
        self.I_serial = 0
        self.I_RG = 0
        self.GD = 0
        self.OG = 0
        self.RD = 0
        self.SpareH = 0
        self.SpareL = 0
        self.Mux0 = 0
        self.Mux1 = 0
        self.Pulse = 0
        self.Mux_enable = 0
    
    
    def set_OD(self, value_V):
        
        value_int = int(value_V // self.ODconv) & 0xff # valid only above 7 V
        self.OD0 = value_int
        self.OD1 = value_int
    
    def set_I_parallel(self, value_int):
    
        self.I_parallel = value_int & 0xff
    
    def set_I_serial(self, value_int):
    
        self.I_serial = value_int & 0xff
    
    def set_I_RG(self, value_int):
        
        self.I_RG = value_int & 0xff
    
    def set_I_clocks(self, value_int):
        
        self.I_parallel = value_int & 0xff
        self.I_serial = value_int & 0xff
        self.I_RG = value_int & 0xff
    
    def set_GD(self, value_V):
        
        value_int = int(value_V // self.GDconv) & 0xff #valid only above 7 V
        self.GD = value_int

    def set_OG(self, value_V):
    
        if (self.OD0 * self.ODconv >= value_V) and (self.OD1 * self.ODconv >= value_V) :
            value_int = int(value_V // self.OGconv) & 0xff
            self.OG = value_int
        else :
            print("Error: trying to set OG higher than OD, cancelled operation")
    
    def set_RD(self, value_V):
        
        value_int = int(value_V // self.RDconv) & 0xff #valid only above 7 V
        self.RD = value_int
    
    def set_cabac_fromstring(self, param, value):
    
        if param == "OD":
            self.set_OD(value)
        elif param == "GD":
            self.set_GD(value)
        elif param == "RD":
            self.set_RD(value)
        elif param == "OG":
            self.set_OG(value)
        elif param == "IP":
            self.set_I_parallel(value)
        elif param == "IS":
            self.set_I_serial(value)
        elif param == "IRG":
            self.set_I_RG(value)
        elif param == "IC":
            self.set_I_clocks(value)
        else :
            raise ValueError("No CABAC parameter with this name: "+ param)
                
                
    def get_cabac_fromstring(self, param):
        
        value = []
        if param == "OD":
            value = [self.OD0 * self.ODconv, self.OD1 * self.ODconv]
        elif param == "GD":
            value = [self.GD * self.GDconv]
        elif param == "RD":
            value = [self.RD * self.RDconv]
        elif param == "OG":
            value = [self.OG * self.OGconv]
        elif param == "IP":
            value = [self.I_parallel]
        elif param == "IS":
            value = [self.I_serial]
        elif param == "IRG":
            value = [self.I_RG]
        elif param == "IC":
            value = [self.I_parallel, self.I_serial, self.I_RG]
        else :
            raise ValueError("No CABAC parameter with this name: "+ param)

        return value

    # ----------------------------------------------------------

    def set_from_registers(self, regs):
        """
        Takes result from CABAC readback and updates the object.
        """
        
        #shortens register keys (suppress geographical information):
        shortregs = {}
        for keyreg in iter(regs):
            shortkey = keyreg & 0xF
            shortregs[shortkey] = regs[keyreg]

        parsed = parse_reg_cabac(shortregs[0])
        self.OD1 = parsed[0]
        self.OD0 = parsed[1]
        self.I_parallel = parse_reg_cabac(shortregs[1])[0]
        parsed = parse_reg_cabac(shortregs[2])
        self.I_RG = parsed[0]
        self.I_serial = parsed[1]
        parsed = parse_reg_cabac(shortregs[3])
        self.SpareH = parsed[0]
        self.RD = parsed[1]
        self.OG = parsed[2]
        self.GD = parsed[3]
        parsed = parse_reg_cabac(shortregs[4])
        ena_s = parsed[1]
        mux_s= parsed[2]
        self.SpareL = parsed[3]
        self.Mux0 = mux_s>>4
        self.Mux1 = mux_s & 0xf
        self.Pulse = ena_s>>7
        self.Mux_enable = (ena_s>>6) & 1

    # ----------------------------------------------------------

    def write_to_registers(self):
        """
        Takes values in the object and writes them in register format
        """
        regs = {}
    
        regs[0] = self.OD1 + (self.OD0 <<8) + (self.OD1 <<16) + (self.OD0 << 24)
        regs[1] = self.I_parallel * 0x1000100010001
        regs[2] = self.I_serial * 0x1000100010000 + self.I_RG
        regs[3] = self.SpareH + (self.RD << 8) + (self.OG << 16) + (self.GD <<24)
        regs[4] = (self.SpareL << 24) + (self.Mux0 << 20) + (self.Mux1 << 16) + (self.Pulse << 15) + (self.Mux_enable << 14)
        
        return regs

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
            header[key] = self.__dict__[field] * self.conv[field]

        header["I_P" + suffix]  = self.I_parallel
        header["I_S" + suffix]  = self.I_serial
        header["I_RG" + suffix] = self.I_RG

        return header

