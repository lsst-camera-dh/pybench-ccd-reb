#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
#
#

import sys
import os, os.path
import re
import subprocess

import cabac
import bidi

## -----------------------------------------------------------------------

class Program(object):
    """
    Internal representation of a 'compiled' FPGA program.
    """

    def __init__(self):
        self.instructions = {}
        self.subroutines = {}

    def __repr__(self):
        s = ""

        addrs = self.instructions.keys()
        addrs.sort()

        last_addr = None
        for addr in addrs:
            if ((last_addr!=None) and (addr != (last_addr + 1))): 
                # empty memory area
                s += "\n"
            s += "0x%03x:     " % addr 
            s += repr(self.instructions[addr])
            s += "\n"
            last_addr = addr

        return s

    def bytecode(self):
        """
        Return the 32 bits byte code for the FPGA compiled program.
        (with relative memory addresses)
        """

        instrs = self.instructions
        addrs = instrs.keys()
        addrs.sort()

        bcs = {}
        for addr in addrs:
            instr = instrs[addr]
            bc = instr.bytecode()
            bcs[addr] = bc

        return bcs

# shortcut
Prg = Program


class Instruction(object):

    OP_CallFunction          = 0x1
    OP_JumpToSubroutine      = 0x2
    OP_ReturnFromSubroutine  = 0x3
    OP_EndOfProgram          = 0x4

    OP_names = { OP_CallFunction          : "CALL",
                 OP_JumpToSubroutine      : "JSR",
                 OP_ReturnFromSubroutine  : "RTS",
                 OP_EndOfProgram          : "END" }

    OP_codes = dict(zip(OP_names.values(), OP_names.keys()))

    pattern_CALL = re.compile(
        "CALL\s+func\((\d+)\)\s+repeat\(((\d+)|infinity)\)")
    pattern_JSR_addr = re.compile(
        "JSR\s+((0[xX])?[\dA-Fa-f]+)\s+repeat\((\d+)\)")
    pattern_JSR_name = re.compile(
        "JSR\s+([\dA-Za-z0-9\_]+)\s+repeat\((\d+)\)")

    def __init__(self, 
                 opcode, 
                 function_id = None, 
                 infinite_loop = False,
                 repeat = 1,
                 address = None,
                 subroutine = None):
        
        self.function_id = 0
        self.address = None
        self.subroutine = None
        self.unassembled = False
        self.repeat = 0
        self.infinite_loop = False

        if opcode in self.OP_codes.keys():
            opcode = self.OP_codes[opcode]

        if opcode not in [self.OP_CallFunction, 
                          self.OP_JumpToSubroutine, 
                          self.OP_ReturnFromSubroutine,
                          self.OP_EndOfProgram]:
            raise ValueError("Invalid FPGA Opcode")

        self.opcode = opcode

        if self.opcode == self.OP_CallFunction:
            if function_id not in range(16):
                raise ValueError("Invalid Function ID")
            if infinite_loop not in [0,1,True,False]:
                raise ValueError("Invalid Infinite Loop flag")
                
            self.function_id = int(function_id) & 0xf
            if infinite_loop:
                self.infinite_loop = True
                self.repeat = 0
            else:
                self.infinite_loop = False
                self.repeat = int(repeat) & ((1<<23) - 1)

        elif self.opcode == self.OP_JumpToSubroutine:
            if address != None:
                self.address = int(address) & ((1<<10) - 1)
            elif subroutine != None:
                self.subroutine = subroutine
            else:
                raise ValueError("Invalid JSR instruction: " +
                                 "no address or subroutine to jump")
                
            # self.infinite_loop = bool(infinite_loop)
            self.repeat = int(repeat) & ((1<<17) - 1)


    def __repr__(self):
        s = ""
        s += "%-4s" % Instruction.OP_names[self.opcode]

        if self.opcode == self.OP_CallFunction:
            s += "    %-11s" % ("func(%d)" % self.function_id) 
            if self.infinite_loop:
                s += "    " + "repeat(infinity)"
            else:
                s += "    " + ("repeat(%d)" % self.repeat)
        elif self.opcode == self.OP_JumpToSubroutine:
            if self.address != None:
                s += "    %-11s" % ("0x%03x" % self.address) 
            else:
                s += "    %-11s" % self.subroutine

            s += "    " + ("repeat(%d)" % self.repeat)

        return s
        

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
            opcode = Instruction.OP_CallFunction
            function_id = int(m.group(1))
            if m.group(2) == "infinity":
                return Instruction(opcode = Instruction.OP_CallFunction,
                                   function_id = function_id,
                                   infinite_loop = True)
            else:
                repeat = int(m.group(2))
                return Instruction(opcode = Instruction.OP_CallFunction,
                                   function_id = function_id,
                                   repeat = repeat)
        
        # JSR addr
        m = cls.pattern_JSR_addr.match(s)
        if m != None:
            opcode = Instruction.OP_JumpToSubroutine
            print m.groups()
            address = int(m.group(1), base=16)
            repeat = int(m.group(3))
            return Instruction(opcode = Instruction.OP_JumpToSubroutine,
                               address = address,
                               repeat = repeat)

        # JSR name
        m = cls.pattern_JSR_name.match(s)
        print m, s
        if m != None:
            opcode = Instruction.OP_JumpToSubroutine
            subroutine = m.group(1)
            repeat = int(m.group(2))
            return Instruction(opcode = Instruction.OP_JumpToSubroutine,
                               subroutine = subroutine,
                               repeat = repeat)

        # RTS
        if s == "RTS":
            opcode = Instruction.OP_ReturnFromSubroutine
            return Instruction(opcode = Instruction.OP_ReturnFromSubroutine)

        # END
        if s == "END":
            opcode = Instruction.OP_EndOfProgram
            return Instruction(opcode = Instruction.OP_EndOfProgram)

        raise ValueError("Unknown instruction")


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
                return Instruction(opcode = opcode,
                                   function_id = function_id,
                                   infinite_loop = infinite_loop,
                                   repeat = 0)
            else:
                # print "repeat", repeat
                return Instruction(opcode = opcode,
                                   function_id = function_id,
                                   repeat = repeat)
                
                
        elif opcode == cls.OP_JumpToSubroutine:
            address = (bc >> 18) & ((1 << 10) - 1)
            # print address
            repeat  = bc & ((1 << 17) - 1)
            # print repeat

            return Instruction(opcode = opcode,
                               address = address,
                               repeat = repeat)

        return Instruction(opcode = opcode)


# shortcut
Instr = Instruction

class Subroutine(object):

    def __init__(self):
        self.name = None
        self.instructions = [] # subroutine instruction list

class Program_UnAssembled(object):
    
    def __init__(self):
        self.subroutines = {} # key = name, value = subroutine object
        self.subroutines_names = [] # to keep the order
        self.instructions = [] # main program instruction list

    # I/O XML -> separate python file
    # I/O text

    def compile(self):
        """
        Compile the program and return the compiled version.
        """
        # subroutines alignment on 0x??0
        alig = 0x010
        
        result = Program()
        subroutines_addr = {}
        
        current_addr = 0x000
        
        # first, the main program
        for instr in self.instructions:
            result.instructions[current_addr] = instr
            current_addr += 1

        # then, each subroutine
        # for subr_name, subr in self.subroutines.iteritems():
        for subr_name in self.subroutines_names:
            subr = self.subroutines[subr_name]
            # alignment
            if current_addr > 0:
                current_addr = (current_addr / alig + 1) * alig
            subroutines_addr[subr_name] = current_addr
            result.subroutines[subr_name] = current_addr
            for instr in subr.instructions:
                result.instructions[current_addr] = instr
                current_addr += 1

        # now setting addresses into JSR_name instructions

        addrs = result.instructions.keys()
        addrs.sort()
        for addr in addrs:
            instr = result.instructions[addr]
            # print addr, instr
            if instr.opcode == Instruction.OP_JumpToSubroutine:
                if not(subroutines_addr.has_key(instr.subroutine)):
                    raise ValueError("Undefine subroutine %s" % 
                                     instr.subroutine)
                # instr.subroutine = None
                instr.address = subroutines_addr[instr.subroutine]
            # print addr, instr
        
        return result


    @classmethod
    def fromstring(cls, s):
        """
        Create a new UnAssembledProgram from a string of instructions.
        """
        lines = s.split("\n")
        nlines = len(lines)
        current_subroutine = None

        prg = Program_UnAssembled()

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

            instr = Instruction.fromstring(s)
            print "INSTR = ", instr
            if instr == None:
                continue

            if current_subroutine != None:
                current_subroutine.instructions.append(instr)
            else:
                prg.instructions.append(instr)
                
            if instr.opcode == Instruction.OP_ReturnFromSubroutine:
                current_subroutine = None

        return prg


    # @classmethod
    # def fromxmlstring(cls, s):
    #     """
    #     Create a new UnAssembledProgram from a XML string.
    #     """
    #     pass


Prg_NA = Program_UnAssembled

## -----------------------------------------------------------------------

class Sequencer(object):
    # 32 outputs are available

    default_channels_desc = {
            0: { 'channel': 0, 
                 'name': 'RU', 
                 'fullname': 'ASPIC ramp-up integration',
                 'FPGA': 'ASPIC_r_up' },
            1: { 'channel': 1, 
                 'name': 'RD', 
                 'fullname': 'ASPIC ramp-down integration',
                 'FPGA': 'ASPIC_r_down' },
            2: { 'channel': 2, 
                 'name': 'RST', 
                 'fullname': 'ASPIC integrator reset',
                 'FPGA': 'ASPIC_reset' },
            3: { 'channel': 3, 
                 'name': 'CL', 
                 'fullname': 'ASPIC clamp',
                 'FPGA': 'ASPIC_clamp' },
            4: { 'channel': 4, 
                 'name': 'R1', 
                 'fullname': 'Serial clock 1',
                 'FPGA': 'CCD_ser_clk(0)' },
            5: { 'channel': 5, 
                 'name': 'R2', 
                 'fullname': 'Serial clock 2',
                 'FPGA': 'CCD_ser_clk(1)' },
            6: { 'channel': 6, 
                 'name': 'R3', 
                 'fullname': 'Serial clock 3',
                 'FPGA': 'CCD_ser_clk(2)' },
            7: { 'channel': 7, 
                 'name': 'RG', 
                 'fullname': 'Serial reset clock',
                 'FPGA': 'CCD_reset_gate' },
            8: { 'channel': 8, 
                 'name': 'P1', 
                 'fullname': 'Parallel clock 1',
                 'FPGA': 'CCD_par_clk(0)' },
            9: { 'channel': 9, 
                 'name': 'P2', 
                 'fullname': 'Parallel clock 2',
                 'FPGA': 'CCD_par_clk(1)' },
            10: { 'channel': 10, 
                  'name': 'P3', 
                  'fullname': 'Parallel clock 3',
                  'FPGA': 'CCD_par_clk(2)' },
            11: { 'channel': 11, 
                  'name': 'P4', 
                  'fullname': 'Parallel clock 4',
                  'FPGA': 'CCD_par_clk(3)' },
            12: { 'channel': 12, 
                  'name': 'SPL', 
                  'fullname': 'ADC sampling signal',
                  'FPGA': 'ADC_trigger' }, 
            13: { 'channel': 13,
                  'name': 'SOI',
                  'fullname': 'Start of Image',
                  'FPGA': 'SOI' },
            14: { 'channel': 14,
                  'name': 'EOI',
                  'fullname': 'End of Image',
                  'FPGA': 'EOI' },
            #
            16: { 'channel': 16, 
                  'name': 'SHU', 
                  'fullname': 'Shutter TTL',
                  'FPGA': 'shutter' }
            }


    default_channels = bidi.BidiMap( [v['channel'] 
                                      for v in default_channels_desc.values()],
                                     [v['name']    
                                      for v in default_channels_desc.values()] )

    def __init__(self, 
                 channels = default_channels, 
                 channels_desc = default_channels_desc, 
                 functions = {}, 
                 functions_desc = {}, 
                 program = Program()):
        #
        self.channels = channels
        self.channels_desc = channels_desc
        self.functions = functions   # max 16 functions (#0 is special)
        self.functions_desc = functions_desc 
        self.program = program       # empty program

    def get_function(self, func):
        if func in range(16):
            func_id = func

        if not(self.functions.has_key(func_id)):
            return None

        return self.functions[func_id]

## -----------------------------------------------------------------------

class Function(object):

    def __init__(self, 
                 name = "", fullname = "", 
                 timelengths = {}, outputs = {}, channels = Sequencer.default_channels):
        # timelengths = id: duration (10ns unit), etc...
        # self.timelengths = {0: 12, 1: 14}
        # self.outputs = {0: '0b01001101...', 1: '0b1111000...', ... }
        self.name = name
        self.fullname = fullname
        self.timelengths = dict(timelengths) # 16 max, (last one zero duration)
        self.outputs = dict(outputs) # bit setup
        self.channels = channels  # mapping bit/symbolic name

        # TODO: add flexibility on the clock line bit map

    def __repr__(self):
        s = "Function: " + self.name + "\n"
        s += "    " + self.fullname + "\n"

        # s += ("                                \t " + 
        #       "               S ESSPPPPRRRRCRRR\n")
        # s += ("slice\t duration (x10ns)\t\t " + 
        #       "               H OOP4321G321LSDU\n")
        # s += ("                        \t\t " + 
        #       "               U IIL|||||||||T||\n")

        l0 = "                                \t "
        l1 = "slice\t duration (x10ns)\t\t "
        l2 = "                        \t\t "

        for i in xrange(32):
            c = 32 - 1 - i
            if self.channels.has_key(c):
                name = self.channels[c]
                named = dict(zip(xrange(len(name)),list(name)))
                l0 += named.get(0, '|')
                l1 += named.get(1, '|')
                l2 += named.get(2, '|')
            else:
                l0 += ' '
                l1 += ' '
                l2 += ' '
            
        s += l0 + '\n' + l1 + '\n' + l2 + '\n'

        s += ( 73 * "-" ) + "\n"
        for sl in xrange(16):
            bit_str = "%032d" % int(bin(self.outputs.get(sl, 0x0))[2:])
            s += "%02d\t %8d\t\t\t %s\n" % ( sl, 
                                             self.timelengths.get(sl, 0), 
                                             bit_str )
        return s

    def is_on(self, channel, timeslice):
        """
        Return the state (0/1) of channel #channel during
        the time slice #timeslice. Return None if undefined.
        """
        if isinstance(channel, str):
            c = self.channels[channel]
        else:
            c = channel

        if self.timelengths.has_key(timeslice):
            state = int( self.outputs[timeslice] & (1<<c) != 0)
            return state

        return None

## -----------------------------------------------------------------------

class FPGA(object):

    # ctrl_host = "lpnws4122"
    # reb_id = 2

    outputs_base_addr = 0x100000
    slices_base_addr  = 0x200000
    program_base_addr = 0x300000
    program_mem_size  = 1024 # ???
    serial_conv = 0.00306 #rough conversion for DACs, no guarantee
    parallel_conv = 0.00348

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host = None, reb_id = 2):
        self.reb_id = reb_id
        self.ctrl_host = ctrl_host
        self.cabac_top = cabac.CABAC()
        self.cabac_bottom = cabac.CABAC()
        self.dacs = {"V_SL":0,"V_SH":0,"V_RGL":0,"V_RGH":0,"V_PL":0,"V_PH":0,"HEAT1":0,"HEAT2":0,"I_OS":0}

    # def open(self):
    #     "Opening the connection ?"
    #     pass

    # def close(self):
    #     pass

    # --------------------------------------------------------------------

    def read(self, address, n = 1, check = True, fake = False):
        """
        Read a FPGA register and return its value.
        if n > 1, returns a list of values.
        """
        # local/remote rriClient invocation... (for the moment)
        # to be replaced

        command = ( "rriClient %d read 0x%0x %d" % (self.reb_id, address, n) )

        if self.ctrl_host == None:
            remote_command = command
        else:
            remote_command = "ssh %s %s" % (self.ctrl_host, command)

        if fake:
            print >>sys.stderr, remote_command
            return dict(zip(range(address, address+n), n * [0]))

            
        proc = subprocess.Popen(remote_command, shell=True,
                                stdout = subprocess.PIPE,
                                stderr = subprocess.PIPE)
        (out, err) = proc.communicate()
        # print err

        # out : 
        # '  Register 0x4 (4): 0x9164efa8 (-1855656024)\n'
        #

        result = {}

        lines = [line.strip() for line in out.split('\n')]

        # print lines

        for line in lines:
            print line
            if line == '': continue
            matches = re.match("Register ([-+]?(0[xX])?[\dA-Fa-f]+) \(([-+]?\d+)\)\: ([-+]?(0[xX])?[\dA-Fa-f]+) \(([-+]?\d+)\)", line)
            if not(matches):
                raise IOError("Failed to read register 0x%0x on REB %d" % (address, reb))
            r = int(matches.group(1), base=16)
            v = int(matches.group(4), base=16)

            result[r] = v

        # if the number of resulting values is different 
        # from the one requested, and check is True, raise an error
        if check and (len(result) < n):
            raise IOError("Failed to read all the requested registers from the FPGA memory")

        return result
                
        
    def write(self, address, value, check = True, fake = False):
        """
        Write a given value into a FPGA register. 
        TODO : implement 'check'
        """
        # "rriClient invocation... (for the moment)
        # to be replaced

        command = ( "rriClient %d write 0x%0x 0x%0x" % 
                    (self.reb_id, address, value) )

        if fake:
            print >>sys.stderr, command
            return

        if self.ctrl_host == None:
            remote_command = command
        else:
            remote_command = "ssh %s %s" % (self.ctrl_host, command)

        proc = subprocess.Popen(remote_command, shell=True,
                                stdout = subprocess.PIPE,
                                stderr = subprocess.PIPE)
        (out, err) = proc.communicate()
        # print err
        # out : 
        # '  Register 0x4 (4): 0x9164efa8 (-1855656024)\n'
        # print err

    # --------------------------------------------------------------------

    def send_program_instruction(self, addr, instr):
        """
        Load the program instruction <instr> at relative address <addr>.
        """
        mem_addr = self.program_base_addr | addr
        bc = instr.bytecode()
        self.write(mem_addr, bc)


    def send_program(self, program, clear = True):
        """
        Load the program <program> into the FPGA program memory.
        """

        # Second, clear the whole memory to avoid mixing with remains
        # of the previous programs

        if clear:
            self.clear_program()
        
        # Load the instructions

        instrs = program.instructions
        addrs = instrs.keys()
        addrs.sort()
        
        for addr in addrs:
            self.send_program_instruction(addr, instrs[addr])



    def dump_program(self):
        """
        Dump the FPGA sequencer program. Return the program.
        """
        prg_addr = FPGA.program_base_addr
        prg_mem = self.read(prg_addr, self.program_mem_size) 
        
        prg = Program()

        addrs = prg_mem.keys()
        addrs.sort()
        
        for addr in addrs:
            bc = prg_mem[addr]
            if (bc != 0x0):
                print "%0x" % addr, "%0x" % bc
                instr = Instruction.frombytecode(bc)
                rel_addr = addr - prg_addr 
                prg.instructions[rel_addr] = instr

        return prg

    def clear_program(self):
        """
        Clear the FPGA sequencer program memory.
        """
        prg_addr = self.program_base_addr
        for i in xrange(self.program_mem_size):
            self.write(prg_addr + i, 0) 
       

    # --------------------------------------------------------------------

    def send_function(self, function_id, function):
        """
        Send the function <function> into the FPGA memory 
        at the #function_id slot.
        """
        if function_id not in range(16):
            raise ValueError("Invalid Function ID")

        slices_addr  = FPGA.slices_base_addr  | (function_id << 4)
        outputs_addr = FPGA.outputs_base_addr | (function_id << 4)

        # Set the given function slices and outputs
        # function #0 -> special case, only the first slice has meaning

        for sl in xrange(16):
            slice_addr = slices_addr | sl
            duration = function.timelengths.get(sl, 0) & 0xffff
            if (function_id == 0) and (sl > 0):
                duration = 0
            self.write(slice_addr, duration)

            output_addr = outputs_addr | sl
            output = function.outputs.get(sl, 0) & 0xffffffff
            if (function_id == 0) and (sl > 0):
                output = 0
            self.write(output_addr, output)


    def send_functions(self, functions):
        for i,f in functions.iteritems():
            self.send_function(i,f)


    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        if function_id not in range(16):
            raise ValueError("Invalid Function ID")

        seq_func = Function()

        # Get time slice lengths

        slices_addr  = FPGA.slices_base_addr  | (function_id << 4)
        outputs_addr = FPGA.outputs_base_addr | (function_id << 4)
        durations = self.read(slices_addr,  16)
        print "durations = ", durations
        outputs   = self.read(outputs_addr, 16)
        print "outputs", outputs

        for sl in xrange(16):
            slice_addr = slices_addr | sl
            print slice_addr, durations[slice_addr]
            seq_func.timelengths[sl] = durations[slice_addr]
        
            # Get the 32 outputs for this timeslice

            output_addr = outputs_addr | sl
            print output_addr, outputs[output_addr]
            seq_func.outputs[sl] = outputs[output_addr]

        return seq_func

    def dump_functions(self):
        """
        Dump all functions from the FPGA memory.
        """
        funcs = {}
        for i in xrange(16):
            funcs[i] = self.dump_function(i)
        return funcs

    # --------------------------------------------------------------------

    def set_image_size(self, size):
        """
        Set image size (in ADC count).
        """
        # rriClient 2 write 0x400005 0x0010F3D8
        self.write(0x400005, size)

    # --------------------------------------------------------------------

    def send_sequencer(self, seq, clear = True):
        """
        Load the functions and the program at once.
        """
        # self.send_program(seq.program, clear = clear)
        print >>sys.stderr, "Loading the sequencer program..."
        self.send_program(seq.program, clear = clear)
        print >>sys.stderr, "Loading the sequencer program done."

        print >>sys.stderr, "Loading the sequencer functions..."
        self.send_functions(seq.functions)
        print >>sys.stderr, "Loading the sequencer functions done."

    def dump_sequencer(self):
        """
        Dump the sequencer program and the 16 functions from the FPGA memory.
        """
        seq = Sequencer()
        seq_prg = self.dump_program()
        seq.program = seq_prg
        for func_id in xrange(16):
            seq_func = self.dump_function(func_id)
            seq.functions[func_id] = seq_func

        return seq

    # ----------------------------------------------------------

    def get_schema(self):
        addr = 0x0
        result = self.read(address = addr)
        if not(result.has_key(addr)):
            raise IOError("Failed to read FPGA memory at address " + str(addr))
        return result[addr]

    schema = property(get_schema, "FPGA address map version")

    # ----------------------------------------------------------

    def get_version(self):
        addr = 0x1
        result = self.read(address = addr)
        if not(result.has_key(addr)):
            raise IOError("Failed to read FPGA memory at address " + str(addr))
        return result[addr]

    version = property(get_version, "FPGA VHDL version")

    # ----------------------------------------------------------

    def get_sci_id(self):
        addr = 0x2
        result = self.read(address = addr)
        if not(result.has_key(addr)):
            raise IOError("Failed to read FPGA memory at address " + str(addr))
        return result[addr]

    sci_id = property(get_sci_id, "SCI's own address")
        
    # ----------------------------------------------------------

    def get_state(self):
        addr = 0x8
        result = self.read(address = addr)
        if not(result.has_key(addr)):
            raise IOError("Failed to read FPGA memory at address " + str(addr))
        return result[addr]

    state = property(get_state, "FPGA state")

    # ----------------------------------------------------------

    def set_trigger(self, trigger):
        self.write(0x9, trigger)

    # ----------------------------------------------------------

    def start_clock(self):
        """
        Start the FPGA internal clock counter.
        """
        st = self.get_state()
        self.set_trigger(st | 0x2)

    def stop_clock(self):
        """
        Stop the FPGA internal clock counter.
        """
        st = self.get_state()
        self.set_trigger(st ^ 0x2)


    def get_time(self):
        result = self.read(address = 0x4, n = 2)
        t = (result[0x5] << 32) | result[0x4]
        return t

    def set_time(self, t):
        up_word = (t>>32) & ((1<<32) - 1)
        lo_word = t & ((1<<32) - 1)
        self.write(address = 0x4, value = lo_word)
        self.write(address = 0x5, value = up_word)

    time = property(get_time, set_time, 
                    "FPGA current time (internal clock, in 10ns units)")

    # ----------------------------------------------------------

    def start(self):
        """
        Start the sequencer program.
        """
        st = self.get_state()
        self.set_trigger(st | 0x4)

    def stop(self):
        """
        Send the command STOP.
        """
        self.write(0x310000, 1)

    def step(self):
        """
        Send the command STEP.
        """
        self.write(0x320000, 1)

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

    def get_board_temperatures(self):
        st = self.get_state()
        self.set_trigger(st | 0x10)
        n_sensors = 10
        raw = self.read(0x600010, n_sensors)
        temperatures = {}
        for i in xrange(n_sensors):
            temperatures[i] = raw[0x600010 + i] * 0.0078
        return raw, temperatures

    # ----------------------------------------------------------

    def get_input_voltages_currents(self):
        st = self.get_state()
        self.set_trigger(st | 0x08)
        raw = self.read(0x600000, 8)
        voltages = {}
        currents = {}

        # 0x600000 6V voltage
        voltages["6V"]  = ((raw[0x600000] & 0xfff0)>>4) * 0.025 # 25 mV
        # 0x600001 6V current
        currents["6V"]  = ((raw[0x600001] & 0xfff0)>>4) * 250e-6 # 25 uA (250 uA in reality ?)

        # 0x600002 9V voltage
        voltages["9V"]  = ((raw[0x600002] & 0xfff0)>>4) * 0.025 # 25 mV
        # 0x600003 9V current
        currents["9V"]  = ((raw[0x600003] & 0xfff0)>>4) * 250e-6 # 25 uA (250 uA in reality ?)

        # 0x600004 24V voltage
        voltages["24V"] = ((raw[0x600004] & 0xfff0)>>4) * 0.025 # 25 mV
        # 0x600005 24V current
        currents["24V"] = ((raw[0x600005] & 0xfff0)>>4) * 80e-6  # 8 uA (80 uA in reality ?)

        # 0x600006 40V voltage
        voltages["40V"] = ((raw[0x600006] & 0xfff0)>>4) * 0.025 # 25 mV
        # 0x600007 40V current
        currents["40V"] = ((raw[0x600007] & 0xfff0)>>4) * 80e-6  # 8 uA (80 uA in reality ?)

        return raw, voltages, currents
    
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

    def set_current_source(self, currents, ccdnum = 0):
        """
        Sets current source DAC value for given CCD (0, 1, 2).
        """
        
        key = "I_OS"
        
        if key in currents:
            self.dacs[key] = currents[key] & 0xfff
        else:
            raise ValueError(
                "No key found for current source (%s), could not be set." % key)
            
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

    def get_cabac_config(self, s): # strip 's'
        """
        read CABAC configuration for strip <s>,
        store it in the CABAC objects and the header string.
        """
        if s not in [0,1,2]:
            raise ValueError("Invalid REB strip (%d)" % s)

        self.write(0x500001, s) # starts the CABAC config readout

        top_config    = self.read(0x500110, 5) # 0 - 4
        bottom_config = self.read(0x500120, 5) # 0 - 4

        self.cabac_top.set_from_registers(top_config)
        self.cabac_bottom.set_from_registers(bottom_config)

        config = self.cabac_top.get_header("T")
        config.update(self.cabac_bottom.get_header("B"))
            
        return config

    # ----------------------------------------------------------

    def set_cabac_config(self, s): # strip 's'
        """
        Writes the current CABAC objects to the FPGA registers
        """
        if s not in [0,1,2]:
            raise ValueError("Invalid REB strip (%d)" % s)
        
        regs_top = self.cabac_top.write_to_registers()
        regs_bottom = self.cabac_bottom.write_to_registers()
        
        for regnum in range(0,5):
            self.write(0x500010 + regnum, regs_top[regnum])
            self.write(0x500020 + regnum, regs_bottom[regnum])
        
        self.write(0x500000, s) # starts the CABAC configuration

    # ----------------------------------------------------------

    def set_cabac_value(self, param, value):
        """
        Sets the CABAC parameter at the given value on both CABACs.
        """
    
        self.cabac_top.set_cabac_fromstring(param, value)
        self.cabac_bottom.set_cabac_fromstring(param, value)

    # ----------------------------------------------------------

    def check_cabac_value(self, param, value):
        """
        Gets the current value of the CABAC objects 
        for the given parameter and checks that it is correct.
        """
        prgm = ( self.cabac_top.get_cabac_fromstring(param) + 
                 self.cabac_bottom.get_cabac_fromstring(param) )

        for prgmval in prgm:
            if (abs(prgmval - value)>0.2):
                raise StandardError(
                    "CABAC readback different from setting for %s: %f != %f" % 
                    (param, prgmval, value) )


    # ----------------------------------------------------------
