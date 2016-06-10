#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
#
#
"""
This is for generic FPGA commands that are common to all versions.
"""

import sys
import re
import subprocess
import time
import bidi

# import gc # trying to avoid fork crash

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
            if last_addr is not None and (addr != (last_addr + 1)):
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


class SequencerPointer(object):

    Pointer_types = ['MAIN', 'PTR_FUNC', 'REP_FUNC', 'PTR_SUBR', 'REP_SUBR']
    Exec_pointers = ['PTR_FUNC', 'PTR_SUBR', 'MAIN']
    Repeat_pointers = ['REP_FUNC', 'REP_SUBR']

    # we are using the dictionary instead
    #Execute_Address = 0x340000
    # these four should be incremented when a pointer is added
    #Ptr_Func_Base = 0x350000
    #Rep_Func_Base = 0x360000
    #Ptr_Subr_Base = 0x370000
    #Rep_Subr_Base = 0x380000

    Mapping_Ptr = dict(zip(Pointer_types,
                           [0x340000, 0x350000, 0x360000, 0x370000, 0x380000]))

    def __init__(self, pointertype, name, value=None, target=''):
        """
        Creates the pointer, associating name and location, and initializing content.
        If not available, use target name and compile later.
        Note that target and value are not expected to match later (for now).
        :param pointertype:
        :param name:
        :param value: value inside the pointer
        :param target: what we are targeting
        :return:
        """
        if pointertype in self.Pointer_types:
            self.pointer_type = pointertype
        else:
            raise ValueError('Attempting to create pointer with unknown type: %s' % pointertype)
        self.name = name

        if self.pointer_type == 'MAIN':
            self.address = self.Mapping_Ptr['MAIN']
        else:
            ptr_address = self.Mapping_Ptr[self.pointer_type]
            self.address = ptr_address

            if (ptr_address & 0xFF) < 16:
                # this increments the base address for the next instance of the class
                self.Mapping_Ptr[self.pointer_type] += 1
            else:
                raise ValueError('Error: registry for pointers %s is full' % self.pointer_type)

        if value is not None:
            self.value = value
            self.target = target
            #debug
            print('Setting pointer %s at address %x with value %d' % (self.name, self.address, self.value))
        elif target:
            self.target = target
            #debug
            print('Setting pointer %s at address %x with target %s' % (self.name, self.address, self.target))
        else:
            raise ValueError('Badly defined pointer: %s, %s' % (pointertype, name))

    def __repr__(self):
        s = "%s %x %s -> " % (self.pointer_type, self.address, self.name)
        if self.value is not None:
            s += "%d " % self.value
        else:
            s += " Undef "
        if self.target:
            s += '(%s)' % self.target

        return s

    def ptr_num(self):
        # address stripped of base address
        return self.address & 0xF

    @classmethod
    def init_addresses(cls):
        """
        Initialize addresses for all pointers to the base values.
        :return:
        """

        cls.Mapping_Ptr = dict(zip(cls.Pointer_types,
                           [0x340000, 0x350000, 0x360000, 0x370000, 0x380000]))


class Instruction(object):

    OP_CallFunction          = 0x1
    OP_CallPointerFunction   = 0x2
    OP_CallFuncPointerRepeat = 0x3
    OP_CallPointerFuncPointerRepeat = 0x4
    OP_JumpToSubroutine      = 0x5
    OP_JumpPointerSubroutine = 0x6
    OP_JumpSubPointerRepeat  = 0x7
    OP_JumpPointerSubPointerRepeat = 0x8
    OP_ReturnFromSubroutine  = 0xE
    OP_EndOfProgram          = 0xF

    OP_names = ["CALL", 'CALLP', 'CALLREP', 'CALLPREP',
                "JSR", 'JSP', 'JSREP', 'JSPREP',
                "RTS", "END"]

    OP_codes = bidi.BidiMap(OP_names,
                            [OP_CallFunction,
                             OP_CallPointerFunction,
                             OP_CallFuncPointerRepeat,
                             OP_CallPointerFuncPointerRepeat,
                             OP_JumpToSubroutine,
                             OP_JumpPointerSubroutine,
                             OP_JumpSubPointerRepeat,
                             OP_JumpPointerSubPointerRepeat,
                             OP_ReturnFromSubroutine,
                             OP_EndOfProgram])
    Call_codes = [OP_CallFunction, OP_CallPointerFunction, OP_CallFuncPointerRepeat, OP_CallPointerFuncPointerRepeat]
    Jsr_codes = [OP_JumpToSubroutine, OP_JumpPointerSubroutine, OP_JumpSubPointerRepeat, OP_JumpPointerSubPointerRepeat]
    SubAddressShift = 16

    pattern_CALL = re.compile(
        "CALL\s+func\((\d+)\)\s+repeat\(((\d+)|infinity)\)")
    pattern_JSR_addr = re.compile(
        "JSR\s+((0[xX])?[\dA-Fa-f]+)\s+repeat\((\d+)\)")
    pattern_JSR_name = re.compile(
        "JSR\s+([\dA-Za-z0-9\_]+)\s+repeat\((\d+)\)")

    def __init__(self,
                 opcode,
                 function_id=None,
                 infinite_loop=False,
                 repeat=1,
                 address=None,
                 subroutine=None):
        """
        The input opcode is the name of the operation or the code value.
        The name goes to self.name, self.opcode is the actual code.
        :param opcode: string or int
        :param function_id: int
        :param infinite_loop: bool or int
        :param repeat: int
        :param address: int
        :param subroutine: string
        :return:
        """
        self.function_id = 0
        self.address = None
        self.subroutine = None
        self.unassembled = False
        self.repeat = 0
        self.infinite_loop = False
        self.opcode = None
        self.name = None

        if opcode in self.OP_names:
            # by name
            self.name = opcode
            self.opcode = self.OP_codes[opcode]
        elif self.OP_codes.has_key(opcode):
            # by opcode value
            self.opcode = opcode
            self.name = self.OP_codes[opcode]
        else:
            raise ValueError("Invalid FPGA OPcode " + opcode.__repr__())

        if self.opcode in self.Call_codes:
            if function_id not in range(16):
                raise ValueError("Invalid Function ID")
            if infinite_loop not in [0, 1, True, False]:
                raise ValueError("Invalid Infinite Loop flag")

            self.function_id = int(function_id) & 0xf
            if infinite_loop:
                self.infinite_loop = True
                self.repeat = 0
            else:
                self.infinite_loop = False
                self.repeat = int(repeat) & 0x3fffff

        elif self.opcode in self.Jsr_codes:
            if address is not None:
                self.address = int(address) & 0x3ff
            elif subroutine is not None:
                self.subroutine = subroutine
            else:
                raise ValueError("Invalid JSR instruction: " +
                                 "no address or subroutine to jump")

            self.repeat = int(repeat) & 0xffff

    def __repr__(self):
        s = ""
        s += "%-8s" % self.name

        if self.opcode in self.Call_codes:
            s += "    %-11s" % ("func(%d)" % self.function_id)
            if self.infinite_loop:
                s += "    " + "repeat(infinity)"
            else:
                s += "    " + ("repeat(%d)" % self.repeat)
        elif self.opcode in self.Jsr_codes:
            if self.address is not None:
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

        if self.opcode in self.Call_codes:
            bc |= (self.function_id & 0xf) << 24

            if self.infinite_loop:
                bc |= 1 << 23
            else:
                bc |= (self.repeat & 0x3fffff)

        elif self.opcode in self.Jsr_codes:
            if self.address == None:
                raise ValueError("Unassembled JSR instruction. No bytecode")

            bc |= (self.address & 0x3ff) << self.SubAddressShift
            bc |= (self.repeat & ((1 << self.SubAddressShift) - 1))

        elif self.opcode in [self.OP_ReturnFromSubroutine,
                             self.OP_EndOfProgram]:
            # OK
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
        # TODO: still missing the new instructions
        # looking for a comment part and remove it

        pos = s.find('#')
        if pos != -1:
            s = s[:pos]

        s = s.strip()
        if len(s) == 0:
            return None

        # CALL
        m = cls.pattern_CALL.match(s)
        if m is not None:
            function_id = int(m.group(1))
            if m.group(2) == "infinity":
                return Instruction(opcode="CALL",
                                   function_id=function_id,
                                   infinite_loop=True)
            else:
                repeat = int(m.group(2))
                return Instruction(opcode="CALL",
                                   function_id=function_id,
                                   repeat=repeat)

        # JSR addr
        m = cls.pattern_JSR_addr.match(s)
        if m is not None:
            print m.groups()
            address = int(m.group(1), base=16)
            repeat = int(m.group(3))
            return Instruction(opcode="JSR",
                               address=address,
                               repeat=repeat)

        # JSR name
        m = cls.pattern_JSR_name.match(s)
        print m, s
        if m is not None:
            subroutine = m.group(1)
            repeat = int(m.group(2))
            return Instruction(opcode="JSR",
                               subroutine=subroutine,
                               repeat=repeat)

        # RTS
        if s == "RTS":
            return Instruction(opcode=s)

        # END
        if s == "END":
            return Instruction(opcode=s)

        raise ValueError("Unknown instruction %s" % s)

    @classmethod
    def frombytecode(cls, bc):
        # Opcode
        opcode = (bc >> 28)
        if opcode not in [cls.OP_CallFunction,
                          cls.OP_CallPointerFunction,
                          cls.OP_CallFuncPointerRepeat,
                          cls.OP_CallPointerFuncPointerRepeat,
                          cls.OP_JumpToSubroutine,
                          cls.OP_JumpPointerSubroutine,
                          cls.OP_JumpSubPointerRepeat,
                          cls.OP_JumpPointerSubPointerRepeat,
                          cls.OP_ReturnFromSubroutine,
                          cls.OP_EndOfProgram]:
            raise ValueError("Invalid FPGA bytecode (invalid opcode)")

        if opcode in cls.Call_codes:
            function_id = (bc >> 24) & 0xf
            infinite_loop = (bc & (1 << 23)) != 0
            # print infinite_loop
            repeat = (bc & 0x3fffff)
            # print repeat

            if infinite_loop:
                # print "infinity"
                return Instruction(opcode=opcode,
                                   function_id=function_id,
                                   infinite_loop=infinite_loop,
                                   repeat=0)
            else:
                # print "repeat", repeat
                return Instruction(opcode=opcode,
                                   function_id=function_id,
                                   repeat=repeat)

        elif opcode == cls.Jsr_codes:
            address = (bc >> cls.SubAddressShift) & 0x3ff
            # print address
            repeat = bc & ((1 << cls.SubAddressShift) - 1)
            # print repeat

            return Instruction(opcode=opcode,
                               address=address,
                               repeat=repeat)

        return Instruction(opcode=opcode)


class Subroutine(object):
    def __init__(self):
        self.name = None
        self.instructions = []  # subroutine instruction list


class Program_UnAssembled(object):
    def __init__(self):
        self.subroutines = {}  # key = name, value = subroutine object
        self.subroutines_names = []  # to keep the order
        self.instructions = []  # main program instruction list
        self.seq_pointers = {}  # pointers (if applicable)

    # I/O XML -> separate python file
    # I/O text -> separate python file

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

        # now setting addresses into JSR/JSREP instructions referring subroutine names
        addrs = result.instructions.keys()
        addrs.sort()
        for addr in addrs:
            instr = result.instructions[addr]
            # print addr, instr
            if instr.name in ['JSR', 'JSREP']:
                if not (subroutines_addr.has_key(instr.subroutine)):
                    raise ValueError("Undefined subroutine %s" %
                                     instr.subroutine)
                # instr.subroutine = None
                instr.address = subroutines_addr[instr.subroutine]
                # print addr, instr

        # also setting pointers referencing subroutines if there are any
        for ptrname in self.seq_pointers:
            seq_pointer = self.seq_pointers[ptrname]
            if seq_pointer.pointer_type in ['MAIN', 'PTR_SUBR']:
                if not (subroutines_addr.has_key(seq_pointer.target)):
                    raise ValueError("Pointer to undefined subroutine %s" %
                                     seq_pointer.target)
                seq_pointer.value = subroutines_addr[seq_pointer.target]

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
            print iline + 1
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
            if instr is None:
                continue

            if current_subroutine is not None:
                current_subroutine.instructions.append(instr)
            else:
                prg.instructions.append(instr)

            if instr.opcode == Instruction.OP_ReturnFromSubroutine:
                current_subroutine = None

        return prg


        # @classmethod
        # def fromxmlstring(cls, s):
        # """
        #     Create a new UnAssembledProgram from a XML string.
        #     """
        #     pass


Prg_NA = Program_UnAssembled

# # -----------------------------------------------------------------------


class Sequencer(object):
    # 32 outputs are available

    default_channels_desc = {
        0: {'channel': 0,
            'name': 'RU',
            'fullname': 'ASPIC ramp-up integration',
            'FPGA': 'ASPIC_r_up'},
        1: {'channel': 1,
            'name': 'RD',
            'fullname': 'ASPIC ramp-down integration',
            'FPGA': 'ASPIC_r_down'},
        2: {'channel': 2,
            'name': 'RST',
            'fullname': 'ASPIC integrator reset',
            'FPGA': 'ASPIC_reset'},
        3: {'channel': 3,
            'name': 'CL',
            'fullname': 'ASPIC clamp',
            'FPGA': 'ASPIC_clamp'},
        4: {'channel': 4,
            'name': 'R1',
            'fullname': 'Serial clock 1',
            'FPGA': 'CCD_ser_clk(0)'},
        5: {'channel': 5,
            'name': 'R2',
            'fullname': 'Serial clock 2',
            'FPGA': 'CCD_ser_clk(1)'},
        6: {'channel': 6,
            'name': 'R3',
            'fullname': 'Serial clock 3',
            'FPGA': 'CCD_ser_clk(2)'},
        7: {'channel': 7,
            'name': 'RG',
            'fullname': 'Serial reset clock',
            'FPGA': 'CCD_reset_gate'},
        8: {'channel': 8,
            'name': 'P1',
            'fullname': 'Parallel clock 1',
            'FPGA': 'CCD_par_clk(0)'},
        9: {'channel': 9,
            'name': 'P2',
            'fullname': 'Parallel clock 2',
            'FPGA': 'CCD_par_clk(1)'},
        10: {'channel': 10,
             'name': 'P3',
             'fullname': 'Parallel clock 3',
             'FPGA': 'CCD_par_clk(2)'},
        11: {'channel': 11,
             'name': 'P4',
             'fullname': 'Parallel clock 4',
             'FPGA': 'CCD_par_clk(3)'},
        12: {'channel': 12,
             'name': 'SPL',
             'fullname': 'ADC sampling signal',
             'FPGA': 'ADC_trigger'},
        13: {'channel': 13,
             'name': 'SOI',
             'fullname': 'Start of Image',
             'FPGA': 'SOI'},
        14: {'channel': 14,
             'name': 'EOI',
             'fullname': 'End of Image',
             'FPGA': 'EOI'},
        #
        16: {'channel': 16,
             'name': 'SHU',
             'fullname': 'Shutter TTL',
             'FPGA': 'shutter'}
    }

    default_channels = bidi.BidiMap([v['channel']
                                     for v in default_channels_desc.values()],
                                    [v['name']
                                     for v in default_channels_desc.values()])

    def __init__(self,
                 channels=default_channels,
                 channels_desc=default_channels_desc,
                 functions={},
                 functions_desc={},
                 program=Program(),
                 parameters={},
                 pointers={}):
        #
        self.channels = channels
        self.channels_desc = channels_desc
        self.functions = functions  # max 16 functions (#0 is special)
        self.functions_desc = functions_desc
        self.program = program  # empty program
        self.parameters = parameters  # memory of the parameter values set in XML/txt
        self.pointers = pointers  # memory of pointers set in txt

    def get_function(self, func):
        if func in range(16):
            func_id = func

        if not (self.functions.has_key(func_id)):
            return None

        return self.functions[func_id]

    def pointer_value(self, typeptr, numptr):
        """
        Returns the pointer content for a given pointer type and number.
        :param typeptr:
        :param numptr:
        :return:
        """
        value = 0
        for pname in self.pointers:
            p = self.pointers[pname]
            if p.pointer_type == typeptr and p.ptr_num() == numptr:
                value = p.value
                break

        return value

    def recurse_time(self, start_address, clockperiod, recurse_level=0):
        """
        Auxiliary for recursivity in timing().
        :param start_adress:
        :return:
        """
        current_address = start_address
        total_time = 0
        strlevel = '\t' * recurse_level

        while current_address in self.program.instructions:
            instr = self.program.instructions[current_address]
            if instr.opcode in instr.Call_codes:
                # parse repetitions, look up function
                if instr.opcode in [instr.OP_CallFunction, instr.OP_CallPointerFunction]:
                    repetitions = instr.repeat
                else:
                    repetitions = self.pointer_value('REP_FUNC', instr.repeat)
                if instr.opcode in [instr.OP_CallFunction, instr.OP_CallFuncPointerRepeat]:
                    funcnum = instr.function_id
                else:
                    funcnum = self.pointer_value('PTR_FUNC', instr.function_id)
                instr_time = self.functions[funcnum].total_time() * repetitions * clockperiod
                total_time += instr_time

            elif instr.opcode in instr.Jsr_codes:
                # parse repetitions, look up new address, iterate
                if instr.opcode in [instr.OP_JumpToSubroutine, instr.OP_JumpPointerSubroutine]:
                    repetitions = instr.repeat
                else:
                    repetitions = self.pointer_value('REP_SUBR', instr.repeat)
                if instr.opcode in [instr.OP_JumpToSubroutine, instr.OP_JumpSubPointerRepeat]:
                    target_address = instr.address
                else:
                    target_address = self.pointer_value('PTR_SUBR', instr.address)
                instr_time = self.recurse_time(target_address, clockperiod, recurse_level=recurse_level+1) \
                             * repetitions
                total_time += instr_time

            else:
                print('%s%s  run total: %f us' % (strlevel, instr.__repr__(), total_time))
                break

            # print here to get total after breakout for calls to subroutines
            print('%s%s  run time: %.2f us  run total: %.2f us' % (strlevel, instr.__repr__(), instr_time, total_time))
            current_address += 1

        return total_time

    def timing(self, subr):
        """
        Computes timing for a given subroutine, with breakout by instruction.
        :param subr:
        :return:
        """
        # will need this, converts to us
        p = self.parameters['clockperiod'] * 1e6

        if subr not in self.program.subroutines:
            print('Unknown subroutine name: %s' % subr)
            return ''

        start_address = self.program.subroutines[subr]
        return self.recurse_time(start_address, p)

## -----------------------------------------------------------------------

class Function(object):
    def __init__(self,
                 name="", fullname="",
                 timelengths={}, outputs={}, channels=Sequencer.default_channels):
        # timelengths = id: duration (10ns unit), etc...
        # self.timelengths = {0: 12, 1: 14}
        # self.outputs = {0: '0b01001101...', 1: '0b1111000...', ... }
        self.name = name
        self.fullname = fullname
        self.timelengths = dict(timelengths)  # 16 max, (last one zero duration)
        self.outputs = dict(outputs)  # bit setup
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
                named = dict(zip(xrange(len(name)), list(name)))
                l0 += named.get(0, '|')
                l1 += named.get(1, '|')
                l2 += named.get(2, '|')
            else:
                l0 += ' '
                l1 += ' '
                l2 += ' '

        s += l0 + '\n' + l1 + '\n' + l2 + '\n'

        s += (73 * "-") + "\n"
        for sl in xrange(16):
            bit_str = "%032d" % int(bin(self.outputs.get(sl, 0x0))[2:])
            s += "%02d\t %8d\t\t\t %s\n" % (sl,
                                            self.timelengths.get(sl, 0),
                                            bit_str)
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
            state = int(self.outputs[timeslice] & (1 << c) != 0)
            return state

        return None

    def total_time(self):
        """
        Returns total duration of functions (expressed as clock cycles).
        Takes into account additionnal cycles at beginning and end.
        :return:
        """
        return sum(self.timelengths.itervalues())+3

## -----------------------------------------------------------------------


class MetaData(object):
    """
    To produce meta-data in the format accepted by the testbench.
    """

    def __init__(self, orderkeys, dictvalues={}, dictcomments={}, name=''):
        self.name = name
        self.keys = orderkeys
        self.values = {}
        self.comments = {}
        for k in self.keys:
            if k in dictvalues:
                self.values[k] = dictvalues[k]
            else:
                self.values[k] = ''
            if k in dictcomments:
                self.comments[k] = dictcomments[k]
            else:
                self.comments[k] = ''

    def __repr__(self):
        s = 'MetaData object %s:\n' % self.name
        s += 'keys    = values               # comments\n'
        for key in self.keys:
            s += '%-8s= %-20s # %s\n' % (key, str(self.values[key]), self.comments[key])
        return s

    def update_single_data(self, key, value, comment=""):
        """
        Adds or updates a single element in the meta-data.
        :param key: string
        :param value:
        :param comment: string
        :return:
        """
        if key not in self.keys:
            self.keys.append(key)
        self.values[key] = value
        self.comments[key] = comment

    def update_fromdict(self, dictvalues, dictcomments={}):
        """
        Add a number of data from a dictionary of values, plus optional comments.
        Note that this overwrites the meta-data if it existed before.
        :param dictvalues: dict
        :param dictcomments: dict
        :return:
        """
        for k in dictvalues:
            if k not in self.keys:
                self.keys.append(k)
            if k in dictcomments:
                self.comments[k] = dictcomments[k]
            else:
                self.comments[k] = ''

        self.values.update(dictvalues)

    def update_ordered(self, orderkeys, dictvalues, dictcomments={}):
        """
        Add a number of data from a dictionary of values, plus optional comments,
        and puts the keys in the order given.
        Note that this appends the meta-data only if the keys are in orderkeys.
        :param orderkeys: list
        :param dictvalues: dict
        :param dictcomments: dict
        :return:
        """
        for k in orderkeys:
            if k in self.keys:
                self.keys.remove(k)
            self.keys.append(k)
            if k in dictvalues:
                self.values[k] = dictvalues[k]
            else:
                self.values[k] = ''
            if k in dictcomments:
                self.comments[k] = dictcomments[k]
            else:
                self.comments[k] = ''

    def update(self, addmeta):
        """
        Updates from another meta object.
        :param addmeta: MetaData
        :return:
        """
        self.update_ordered(addmeta.keys, addmeta.values, addmeta.comments)

    def order_keys(self, neworder):
        """
        Re-order the keys in the specified order. If some keys are
        not in the parameter, they are appended at the end in the
        same order as before.
        :param neworder:
        :return:
        """
        for k in neworder:
            if k in self.keys:
                self.keys.remove(k)
            # if not already present, add value and comment for later use
            else:
                self.values[k] = ''
                self.comments[k] = ''
        neworder.extend(self.keys)
        self.keys = neworder


## ----------------------------------------------------------


def check_location(s, loc=3):
    if s not in [0, 1, 2]:
        raise ValueError("Invalid REB stripe (%d)" % s)
    if loc not in [1, 2, 3]:
        raise ValueError("Invalid Location code (%d)" % loc)
    return True


class FPGA(object):
    # ctrl_host = "lpnws4122"
    # reb_id = 2

    outputs_base_addr = 0x100000
    slices_base_addr = 0x200000
    program_base_addr = 0x300000
    program_mem_size = 0x3ff
    n_sensors_boardtemp = 10
    supplies = ['6V', '9V', '24V', '40V']

    # --------------------------------------------------------------------

    def __init__(self, ctrl_host=None, reb_id=2):
        self.reb_id = reb_id
        self.ctrl_host = ctrl_host
        # declare two CABACs and two ASPICs for each stripe even if they will not be used
        # (at least we will want to initialize to 0)

    # --------------------------------------------------------------------

    def read(self, address, n=1, check=True, fake=False, verbose=True):
        """
        Read a FPGA register and return its value.
        if n > 1, returns a list of values.
        """
        # local/remote rriClient invocation... (for the moment)
        # to be replaced

        command = ("rriClient %d read 0x%0x %d" % (self.reb_id, address, n))

        if self.ctrl_host is None:
            remote_command = command
        else:
            remote_command = "ssh %s %s" % (self.ctrl_host, command)

        if fake:
            print >> sys.stderr, remote_command
            return dict(zip(range(address, address + n), n * [0]))

        proc = subprocess.Popen(remote_command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        # print err

        # out : 
        # '  Register 0x4 (4): 0x9164efa8 (-1855656024)\n'
        #

        result = {}

        lines = [line.strip() for line in out.split('\n')]

        # print lines

        for line in lines:
            if verbose:
                print line
            if line == '':
                continue
            matches = re.match(
                "Register ([-+]?(0[xX])?[\dA-Fa-f]+) \(([-+]?\d+)\)\: ([-+]?(0[xX])?[\dA-Fa-f]+) \(([-+]?\d+)\)",
                line)
            if not matches:
                raise IOError("Failed to read register 0x%0x on FPGA" % address)
            r = int(matches.group(1), base=16)
            v = int(matches.group(4), base=16)

            result[r] = v

        # if the number of resulting values is different 
        # from the one requested, and check is True, raise an error
        if check and (len(result) < n):
            raise IOError("Failed to read all the requested registers from the FPGA memory")
        if check and address not in result:
            raise IOError("Failed to read FPGA memory at address " + str(address))

        return result

    def write(self, address, value, check=False, fake=False):
        """
        Write a given value into a FPGA register. 
        TODO : implement 'check'
        """
        # "rriClient invocation... (for the moment)
        # to be replaced

        command = ("rriClient %d write 0x%0x 0x%0x" %
                   (self.reb_id, address, value))

        if fake:
            print >> sys.stderr, command
            return

        if self.ctrl_host is None:
            remote_command = command
        else:
            remote_command = "ssh %s %s" % (self.ctrl_host, command)

        proc = subprocess.Popen(remote_command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        # print err
        # out : 
        # '  Register 0x4 (4): 0x9164efa8 (-1855656024)\n'
        # print err
        # printout for debug
        if check:
            print command

    def write_spi(self, address, stripe, position, register, write=False):
        """
        Writes to an SPI serial link through the FPGA in the format defined for ASPIC and CABAC.
        Position = 1 for bottom, 2 for top.
        :param address: int
        :param stripe: int
        :param position: int
        :param register: int
        :return:
        """
        stripecode = 1 << (26 + stripe)
        positioncode = position << 24
        if write:
            regcode = ((1 << 23) | register) & 0xffffff
        else:
            regcode = register & 0x7fffff
        self.write(address, stripecode + positioncode + regcode)

    # --------------------------------------------------------------------

    def send_program_instruction(self, addr, instr):
        """
        Load the program instruction <instr> at relative address <addr>.
        """
        mem_addr = self.program_base_addr | addr
        bc = instr.bytecode()
        self.write(mem_addr, bc)

    def send_program(self, program, clear=True):
        """
        Load the program <program> into the FPGA program memory.
        """

        instrs = program.instructions
        addrs = instrs.keys()
        addrs.sort()

        # Clear the whole memory to avoid mixing with remains
        # of the previous programs
        # now limited to likely addresses to gain time
        if clear:
            self.clear_program(addrs[-1]+16)

        # Load the instructions
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
            if bc != 0x0:
                print "%0x" % addr, "%0x" % bc
                instr = Instruction.frombytecode(bc)
                rel_addr = addr - prg_addr
                prg.instructions[rel_addr] = instr

        return prg

    def clear_program(self, max_address=0):
        """
        Clear the FPGA sequencer program memory.
        Option: limit to a likely block of addresses.
        """
        prg_addr = self.program_base_addr
        for i in xrange(max_address and max_address or self.program_mem_size):
            self.write(prg_addr + i, 0)

            # --------------------------------------------------------------------

    def send_function(self, function_id, function):
        """
        Send the function <function> into the FPGA memory 
        at the #function_id slot.
        """
        if function_id not in range(16):
            raise ValueError("Invalid Function ID")

        slices_addr = FPGA.slices_base_addr | (function_id << 4)
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
        for i, f in functions.iteritems():
            self.send_function(i, f)

    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        if function_id not in range(16):
            raise ValueError("Invalid Function ID")

        seq_func = Function()

        # Get time slice lengths

        slices_addr = FPGA.slices_base_addr | (function_id << 4)
        outputs_addr = FPGA.outputs_base_addr | (function_id << 4)
        durations = self.read(slices_addr, 16)
        print "durations = ", durations
        outputs = self.read(outputs_addr, 16)
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

    def send_pointer(self, seqpointer):
        """
        Writes one pointer object to the FPGA. It knows its own address.
        :ptype seqpointer: SequencerPointer
        :return:
        """
        self.write(seqpointer.address, seqpointer.value)

    def read_pointer(self, seqpointer):
        """
        Reads a pointer object from the FPGA
        :param seqpointer:
        :return:
        """
        return self.read(seqpointer.address)[seqpointer.address]

    def send_pointers(self, allpointers):
        """
        Sends all pointers.
        :param allpointers:
        :return:
        """
        for seqpointer in allpointers:
            self.send_pointer(allpointers[seqpointer])

    # --------------------------------------------------------------------

    def send_sequencer(self, seq, clear=True):
        """
        Load the functions and the program at once.
        Plus pointers now (empty if does not apply).
        """
        # self.send_program(seq.program, clear = clear)
        print >> sys.stderr, "Loading the sequencer program..."
        self.send_program(seq.program, clear=clear)
        print >> sys.stderr, "Loading the sequencer program done."

        print >> sys.stderr, "Loading the sequencer functions..."
        self.send_functions(seq.functions)
        print >> sys.stderr, "Loading the sequencer functions done."

        print >> sys.stderr, "Loading the pointers..."
        self.send_pointers(seq.pointers)
        print >> sys.stderr, "Loading the pointers done."

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
        result = self.read(address=addr)
        return result[addr]

    schema = property(get_schema, "FPGA address map version")

    # ----------------------------------------------------------

    def get_version(self):
        addr = 0x1
        result = self.read(address=addr)
        return result[addr]

    version = property(get_version, "FPGA VHDL version")

    # ----------------------------------------------------------

    def get_sci_id(self):
        addr = 0x2
        result = self.read(address=addr)
        return result[addr]

    sci_id = property(get_sci_id, "SCI's own address")

    # ----------------------------------------------------------

    def get_state(self):
        addr = 0x8
        result = self.read(address=addr)
        return result[addr]

    state = property(get_state, "FPGA state")

    # ----------------------------------------------------------

    def get_boardID(self):
        """
        Default when no readback available from the board itself.
        :return:
        """
        return str(self.get_sci_id())

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
        Stop the FPGA internal clock counter if it is running.
        """
        st = self.get_state()
        if st & 2:
            st -= 2
        self.set_trigger(st)

    def get_time(self):
        result = self.read(address=0x4, n=2)
        t = (result[0x5] << 32) | result[0x4]
        return t

    def set_time(self, t):
        up_word = (t >> 32) & ((1 << 32) - 1)
        lo_word = t & ((1 << 32) - 1)
        self.write(address=0x4, value=lo_word)
        self.write(address=0x5, value=up_word)

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
        self.write(0x320000, 1)

    def step(self):
        """
        Send the command STEP.
        """
        self.write(0x310000, 1)

    # ----------------------------------------------------------

    def get_board_temperatures(self):
        st = self.get_state()
        self.set_trigger(st | 0x10)
        # trigger will stop autonomously when done
        while self.get_state() & 0x10:
            time.sleep(0.08)  # slight increase to avoid some failures of communication

        raw = self.read(0x600010, self.n_sensors_boardtemp)
        tempkeys = []
        temperatures = {}
        comments = {}

        for i in xrange(self.n_sensors_boardtemp):
            tempkey = 'TREB_%d' % i
            tempkeys.append(tempkey)
            answer = raw[0x600010 + i] 
            if answer & 0x10000:
                print("Warning: error on board temperature measurement %d" % i)
            answer=answer & 0xffff
            #            temperatures[tempkey] = (answer & 0xffff) * 0.0078
            temperatures[tempkey] = (answer-0xFFFF*(answer>>15))*0.0078  
            comments[tempkey] = '[C] REB board temperature sensor %d' % i

        return MetaData(tempkeys, temperatures, comments)

    # ----------------------------------------------------------

    def get_input_voltages_currents(self):
        st = self.get_state()
        self.set_trigger(st | 0x08)
        # trigger will stop when done
        while self.get_state() & 8:
            time.sleep(0.08)
        raw = self.read(0x600000, len(self.supplies) * 2)

        voltages = {}
        currents = {}
        orderkeys = []
        dictvalues = {}
        dictcomments = {}

        for i,v in enumerate(self.supplies):
            if v in ['24V', '40V', 'VDDOD', 'VDDCLK']:
                conv_i = 80e-6  # 8 uA (80 uA in reality ?)
            else:
                conv_i = 250e-6  # 25 uA  in doc, 250 uA in reality
            voltages[v] = round(((raw[0x600000 + i * 2] & 0xfff0) >> 4) * 0.025, 3)  # 25 mV
            currents[v] = round(((raw[0x600001 + i * 2] & 0xfff0) >> 4) * conv_i, 3)
            vstr = 'V_%s' % v
            istr = 'I_%s' % v
            orderkeys.append(vstr)
            orderkeys.append(istr)

            dictvalues[vstr] = voltages[v]
            dictvalues[istr] = currents[v]

            dictcomments[vstr] = '[V] %s power supply voltage' % v
            dictcomments[istr] = '[A] %s power supply current' % v

        return MetaData(orderkeys, dictvalues, dictcomments)

    # ----------------------------------------------------------

    def get_fpga_config(self, s):  # stripe 's'
        """
        Output for header.
        """
        # do not want to stop for reading errors here
        try:
            config = self.get_input_voltages_currents()
        except:
            print("Warning: error while reading power supply voltages and currents")
            config = MetaData([])
        try:
            config.update(self.get_board_temperatures())
        except:
            print("Warning: error while reading board temperatures")

        return config
        
