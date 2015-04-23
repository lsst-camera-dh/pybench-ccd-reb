#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
#
# This one is for REB1 with DREB1. This means CABAC0, ASPIC2 (not managed by the FPGA),
# and first version of the sequencer (with no pointers).
# Take from wreb for more advanced REBs and DREBs.

from py.camera.generic.fpga import *

import cabac0 as cabac

## -----------------------------------------------------------------------

# shortcut
Prg = Program


class Instruction0(Instruction):

    OP_CallFunction          = 0x1
    OP_JumpToSubroutine      = 0x2
    OP_ReturnFromSubroutine  = 0x3
    OP_EndOfProgram          = 0x4

    OP_codes = bidi.BidiMap(Instruction.OP_names,
                            [OP_CallFunction, OP_JumpToSubroutine, OP_ReturnFromSubroutine, OP_EndOfProgram])

    def __init__(self,
                 opcode, 
                 function_id = None, 
                 infinite_loop = False,
                 repeat = 1,
                 address = None,
                 subroutine = None):
        Instruction.__init__(self, opcode, function_id, infinite_loop, repeat, address, subroutine)

    def bytecode(self):
        """
        Return the 32 bits byte code for the FPGA instruction
        """
        
        bc = 0x00000000

        # Opcode
        bc |= (self.opcode & 0xf) << 28

        if self.opcode == self.OP_CallFunction:
            bc |= (self.function_id & 0xf) << 24
            
            if self.infinite_loop:
                bc |= 1 << 23
            else:
                bc |= (self.repeat & ((1<<23) - 1))
                
        elif self.opcode == self.OP_JumpToSubroutine:
            if self.address == None:
                raise ValueError("Unassembled JSR instruction. No bytecode")

            bc |= (self.address & ((1<<10) - 1)) << 18
            bc |= (self.repeat & ((1<<17) - 1))

        elif self.opcode in [ self.OP_ReturnFromSubroutine, 
                              self.OP_EndOfProgram]:
            #OK
            pass
        
        else:
            raise ValueError("Invalid instruction")

        return bc


    @classmethod
    def fromstring(cls, s):
        """
        Create an instruction from a string (without label).
        Return None for an empty string.
        Raise an exception if the syntax is wrong.
        """

        # looking for a comment part and remove it

        pos = s.find('#')
        if pos != -1:
            s = s[:pos]

        s = s.strip()

        if len(s) == 0:
            return None

        # CALL
        m = cls.pattern_CALL.match(s)
        if m != None:
            function_id = int(m.group(1))
            if m.group(2) == "infinity":
                return Instruction0(opcode = "CALL",
                                   function_id = function_id,
                                   infinite_loop = True)
            else:
                repeat = int(m.group(2))
                return Instruction0(opcode = "CALL",
                                   function_id = function_id,
                                   repeat = repeat)

        # JSR addr
        m = cls.pattern_JSR_addr.match(s)
        if m != None:
            print m.groups()
            address = int(m.group(1), base=16)
            repeat = int(m.group(3))
            return Instruction0(opcode = "JSR",
                               address = address,
                               repeat = repeat)

        # JSR name
        m = cls.pattern_JSR_name.match(s)
        print m, s
        if m != None:
            subroutine = m.group(1)
            repeat = int(m.group(2))
            return Instruction0(opcode = "JSR",
                               subroutine = subroutine,
                               repeat = repeat)

        # RTS
        if s == "RTS":
            return Instruction0(opcode = s)

        # END
        if s == "END":
            return Instruction0(opcode = s)

        raise ValueError("Unknown instruction %s" % s)

    @classmethod
    def frombytecode(cls, bc):
        # Opcode
        opcode = (bc >> 28) 
        if opcode not in [cls.OP_CallFunction, 
                          cls.OP_JumpToSubroutine, 
                          cls.OP_ReturnFromSubroutine,
                          cls.OP_EndOfProgram]:
            raise ValueError("Invalid FPGA bytecode (invalid opcode)")

        if opcode == cls.OP_CallFunction:
            function_id = (bc >> 24) & 0xf
            infinite_loop = (bc & (1 << 23)) != 0
            # print infinite_loop
            repeat = (bc & ((1 << 23) - 1))
            # print repeat

            if infinite_loop:
                # print "infinity"
                return Instruction0(opcode = opcode,
                                   function_id = function_id,
                                   infinite_loop = infinite_loop,
                                   repeat = 0)
            else:
                # print "repeat", repeat
                return Instruction0(opcode = opcode,
                                   function_id = function_id,
                                   repeat = repeat)
                
                
        elif opcode == cls.OP_JumpToSubroutine:
            address = (bc >> 18) & ((1 << 10) - 1)
            # print address
            repeat  = bc & ((1 << 17) - 1)
            # print repeat

            return Instruction0(opcode = opcode,
                               address = address,
                               repeat = repeat)

        return Instruction0(opcode = opcode)


# shortcut
Instr = Instruction0

class Program0_UnAssembled(Program_UnAssembled):
    
    def __init__(self):
        Program_UnAssembled.__init__(self)
    # I/O XML -> separate python file
    # I/O text


    @classmethod
    def fromstring(cls, s):
        """
        Create a new UnAssembledProgram from a string of instructions.
        """
        lines = s.split("\n")
        nlines = len(lines)
        current_subroutine = None

        prg = Program0_UnAssembled()

        print lines

        for iline in xrange(nlines):
            print iline+1
            line = lines[iline]
            print line
            elts = line.split()

            if len(elts) < 1:
                # empty line
                continue
            
            # label
            if elts[0][-1] == ':':
                # first elt is a label -> start of a subroutine
                subroutine_name = elts[0][:-1]
                prg.subroutines[subroutine_name] = Subroutine()
                prg.subroutines_names.append(subroutine_name)
                current_subroutine = prg.subroutines[subroutine_name]
                elts = elts[1:]
            
            if len(elts) < 1:
                # empty label
                continue

            s = " ".join(elts)

            instr = Instruction0.fromstring(s)
            print "INSTR = ", instr
            if instr == None:
                continue

            if current_subroutine != None:
                current_subroutine.instructions.append(instr)
            else:
                prg.instructions.append(instr)
                
            if instr.opcode == Instruction0.OP_ReturnFromSubroutine:
                current_subroutine = None

        return prg


    # @classmethod
    # def fromxmlstring(cls, s):
    #     """
    #     Create a new UnAssembledProgram from a XML string.
    #     """
    #     pass


Prg_NA = Program0_UnAssembled

## -----------------------------------------------------------------------

class FPGA0(FPGA):

    # ctrl_host = "lpnws4122"
    # reb_id = 2

    serial_conv = 0.00306 #rough conversion for DACs, no guarantee
    parallel_conv = 0.00348

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host = None, reb_id = 2):
        FPGA.__init__(ctrl_host, reb_id)
        # declare two CABACs for each stripe even if they will not be used
        # (at least we will want to initialize to 0 if they exist)
        self.cabac_top = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.cabac_bottom = [cabac.CABAC(), cabac.CABAC(), cabac.CABAC()]
        self.dacs = {"V_SL":0,"V_SH":0,"V_RGL":0,"V_RGH":0,"V_PL":0,"V_PH":0,"HEAT1":0,"HEAT2":0,"I_OS":0}

    # --------------------------------------------------------------------

    def dump_program(self):
        """
        Dump the FPGA sequencer program. Return the program.
        """
        prg_addr = FPGA0.program_base_addr
        prg_mem = self.read(prg_addr, self.program_mem_size) 
        
        prg = Program()

        addrs = prg_mem.keys()
        addrs.sort()
        
        for addr in addrs:
            bc = prg_mem[addr]
            if (bc != 0x0):
                print "%0x" % addr, "%0x" % bc
                instr = Instruction0.frombytecode(bc)
                rel_addr = addr - prg_addr 
                prg.instructions[rel_addr] = instr

        return prg

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

    # ----------------------------------------------------------

    def set_clock_voltages(self, voltages):
        """
        Sets voltages as defined in the input dictionary, 
        keeps others as previously defined.
        """
        
        #values to be set in the register for each output
        outputnum = {"V_SL":0,"V_SH":1,"V_RGL":2,"V_RGH":3,"V_PL":4,"V_PH":5,"HEAT1":6,"HEAT2":7}

        for key in iter(voltages):
            if key in ["V_SL","V_SH","V_RGL","V_RGH"]:
                self.dacs[key] = int(voltages[key]/self.serial_conv)& 0xfff
            elif key in ["V_PL", "V_PH"]:
                self.dacs[key] = int(voltages[key]/self.parallel_conv)& 0xfff
            elif key in ["HEAT1", "HEAT2"]:
                self.dacs[key] = int(voltages[key]) & 0xfff
            else:
                raise ValueError("Unknown voltage key: %s, could not be set" % key)
            
            self.write(0x400000, self.dacs[key] + (outputnum[key]<<12) )
         
        # activates DAC outputs
        self.write(0x400001, 1)

    # ----------------------------------------------------------

    def get_clock_voltages(self):
        """
        No readback available, using values stored in fpga object.
        """
        fitsheader = {}
        for key in iter(self.dacs):
            if key in ["V_SL","V_SH","V_RGL","V_RGH"]:
                # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.serial_conv)
                fitsheader[key]= self.dacs[key]*self.serial_conv
            elif key in ["V_PL", "V_PH"]:
                # fitsheader[key]= "{:.2f}".format(self.dacs[key]*self.parallel_conv)
                fitsheader[key]= self.dacs[key]*self.parallel_conv
            else:
                # fitsheader[key]= "{:d}".format(self.dacs[key])
                fitsheader[key]= self.dacs[key]

        return fitsheader

    # ----------------------------------------------------------

    def set_current_source(self, current, ccdnum = 0):
        """
        Sets current source DAC value for given CCD (0, 1, 2).
        """
        
        key = "I_OS"

        self.dacs[key] = current & 0xfff

        self.write(0x400010, self.dacs[key] + (ccdnum <<12) )
                
        #activates DAC output
        self.write(0x400011, 1)

    # ----------------------------------------------------------

    def get_current_source(self):
        """
        No readback available, using values stored in fpga object.
        """
        
        key = "I_OS"
    
        return {key: self.dacs[key]}

    # ----------------------------------------------------------

    def get_cabac_config(self, s): # stripe 's'
        """
        read CABAC configuration for stripe <s>,
        store it in the CABAC objects and the header string.
        """
        check_location(s)

        self.write(0x500001, s) # starts the CABAC config readout

        top_config    = self.read(0x500110, 5) # 0 - 4
        bottom_config = self.read(0x500120, 5) # 0 - 4

        self.cabac_top[s].set_from_registers(top_config)
        self.cabac_bottom[s].set_from_registers(bottom_config)

        config = self.cabac_top[s].get_header("%dT" % s)
        config.update(self.cabac_bottom[s].get_header("%dB" % s))
            
        return config

    # ----------------------------------------------------------

    def send_cabac_config(self, s=0): # stripe 's'
        """
        Writes the current CABAC objects of the given stripe to the FPGA registers
        """
        check_location(s)

        regs_top = self.cabac_top[s].write_to_registers()
        regs_bottom = self.cabac_bottom[s].write_to_registers()
        
        for regnum in range(0,5):
            self.write(0x500010 + regnum, regs_top[regnum])
            self.write(0x500020 + regnum, regs_bottom[regnum])
        
        self.write(0x500000, s) # starts the CABAC configuration

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
        prgm = ( self.cabac_top[s].get_cabac_fromstring(param) +
                 self.cabac_bottom[s].get_cabac_fromstring(param) )

        for prgmval in prgm:
            if (abs(prgmval - value)>0.2):
                raise StandardError(
                    "CABAC readback different from setting for %s: %f != %f" %
                    (param, prgmval, value) )


     # ----------------------------------------------------------

    def reset_cabac(self, s=0): # stripe 's'
        """
        Writes 0 to all the FPGA CABAC registers for stripe s
        """
        check_location(s)

        for regnum in range(0,5):
            self.write(0x500010 + regnum, 0)
            self.write(0x500020 + regnum, 0)

        self.write(0x500000, s) # starts the CABAC configuration

    # ASPIC stuff: not needed for REB1+ASPIC2. Take from wreb for REB2/WGREB+ASPIC3.



