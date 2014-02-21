
import fpga


class REB(object):

    # ctrl_host = "lpnws4122"
    # reb_id = 2

    default_functions = None

    default_program = """
main:        JSR     acq            repeat(1)
             END 

acq:         JSR     clear          repeat(2)
             CALL    func(1)        repeat(10000)
             CALL    func(6)        repeat(2048)
             JSR     read_line      repeat(2020)
             RTS 

clear:       JSR     clear_line     repeat(2020)
             RTS 

clear_10:    JSR     clear          repeat(10)
             RTS 

clear_bias:  JSR     clear          repeat(2)
             CALL    func(6)        repeat(550)
             JSR     read_line      repeat(2020)
             RTS 

acq_fake:    JSR     clear          repeat(2)
             CALL    func(1)        repeat(10000)
             CALL    func(6)        repeat(1100)
             JSR     read_line_fake repeat(2020)
             RTS 

bias:        CALL    func(6)        repeat(550)
             JSR     read_line      repeat(2020)
             RTS 

clear_acq:   JSR     clear          repeat(2)
             # exposure while clearing 
             # (call expo_clear: 1 time = 100 us, up to 17 bits, here 4E20 = 2s)
             JSR     expo_clear     repeat(20000)
             # before readout : flush serial register again twice (0x44c)
             CALL    func(6)        repeat(1100)
             JSR     read_line      repeat(2020)
             RTS 

# auxiliary subroutine: exposure while clearing 
# duration 100 us (for consistency with exposure without clearing)

expo_clear:  CALL    func(7)        repeat(50)
             RTS 

read_line:   CALL    func(2)        repeat(1)     # line transfer 
             # read 550 pixels (10 prescan + 512 + 28 overscan)
             CALL    func(3)        repeat(550)   
             RTS 

clear_line:  CALL    func(5)        repeat(1)
             CALL    func(6)        repeat(550)
             RTS 

read_line_fake: 
             CALL    func(2)        repeat(1)     # line transfer 
             # read 550 pixels (10 prescan + 512 + 28 overscan)
             CALL    func(4)        repeat(550)
             RTS 
"""

    def __init__(self, ctrl_host = None, reb_id = 2):
        self.reb_id = reb_id
        self.ctrl_host = ctrl_host
        self.fpga = fpga.FPGA(ctrl_host = self.ctrl_host, 
                              reb_id = self.reb_id)

    # --------------------------------------------------------------------


    # --------------------------------------------------------------------

    def load_function(self, function_id, function):
        """
        Send the function <function> into the FPGA memory 
        at the #function_id slot.
        """
        self.fpga.send_function(function_id, function)

    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        return self.fpga.dump_function(function_id)

    def load_functions(self, functions):
        pass

    # --------------------------------------------------------------------

    def load_program(self, program = default_program):
        """
        Load the compiled program <program> into the FPGA program memory.
        The program may also be provided as an uncompiled text string.
        """
        if isinstance(program, str):
            # Loading the program text
            p_u = fpga.Program_UnAssembled.fromstring(program)
            # compiling it
            program = p_u.compile()
        
        # loading it into the FPGA program memory
        self.fpga.send_program(program)

        self.program = program # to keep it in memory

    def dump_program(self):
        """
        Dump the FPGA sequencer program. Return the program.
        """
        return self.fpga.dump_program()

    def clear_program(self):
        """
        Clear the FPGA sequencer program memory.
        """
        self.fpga.clear_program()

    def run_program(self):
        """
        Trigger the FPGA sequencer program.
        """
        self.fpga.start()

    
    def select_subroutine(self, subname, repeat = 1): 
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.program == None:
            raise ValueError("No program with identified subroutines yet.")

        if not(self.program.subroutines.has_key(subname)):
            raise ValueError("No subroutine '%s' in the FPGA program."
                             % subname)

        first_instr = fpga.Instruction(
            opcode = fpga.Instruction.OP_JumpToSubroutine,
            address = self.program.subroutines[subname],
            repeat = repeat)

        # print first_instr
        # print first_instr.bytecode()

        # load it at the very beginning of the program (rel addr 0x0)
        self.fpga.send_program_instruction(0x0, first_instr)
        self.program.instructions[0x0] = first_instr # to keep it in sync


    def run_subroutine(self, subname, repeat = 1): 
        self.select_subroutine(subname = subname, repeat = repeat)
        self.run_program()

    # --------------------------------------------------------------------


# """
# 0x000:     JSR     0x010          repeat(1)
# 0x001:     END 

# 0x010:     JSR     0x020          repeat(2)
# 0x011:     CALL    func(1)        repeat(10000)
# 0x012:     CALL    func(6)        repeat(2048)
# 0x013:     JSR     0x100          repeat(2020)
# 0x014:     RTS 

# 0x020:     JSR     0x110          repeat(2020)
# 0x021:     RTS 

# 0x030:     JSR     0x020          repeat(10)
# 0x031:     RTS 

# 0x040:     JSR     0x020          repeat(2)
# 0x041:     CALL    func(6)        repeat(550)
# 0x042:     JSR     0x100          repeat(2020)
# 0x043:     RTS 

# 0x050:     JSR     0x020          repeat(2)
# 0x051:     CALL    func(1)        repeat(10000)
# 0x052:     CALL    func(6)        repeat(1100)
# 0x053:     JSR     0x120          repeat(2020)
# 0x054:     RTS 

# 0x060:     CALL    func(6)        repeat(550)
# 0x061:     JSR     0x100          repeat(2020)
# 0x062:     RTS 

# 0x070:     JSR     0x020          repeat(2)
# 0x071:     JSR     0x075          repeat(20000)
# 0x072:     CALL    func(6)        repeat(1100)
# 0x073:     JSR     0x100          repeat(2020)
# 0x074:     RTS 
# 0x075:     CALL    func(7)        repeat(50)
# 0x076:     RTS 

# 0x100:     CALL    func(2)        repeat(1)
# 0x101:     CALL    func(3)        repeat(550)
# 0x102:     RTS 

# 0x110:     CALL    func(5)        repeat(1)
# 0x111:     CALL    func(6)        repeat(550)
# 0x112:     RTS 

# 0x120:     CALL    func(2)        repeat(1)
# 0x121:     CALL    func(4)        repeat(550)
# 0x122:     RTS 
# """
