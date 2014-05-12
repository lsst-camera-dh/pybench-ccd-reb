
import fpga
import time


class REB(object):

    # ctrl_host = "lpnws4122"
    # reb_id = 2

    # loading the functions
    
    # bit 0  : RU  (ASPIC ramp-up integration)
    # bit 1  : RD  (ASPIC ramp-down integration)
    # bit 2  : RST (ASPIC reset)
    # bit 3  : CL  (ASPIC clamp)
    
    # bit 4  : R1  (Serial clock 1)
    # bit 5  : R2  (Serial clock 2)
    # bit 6  : R3  (Serial clock 3)
    # bit 7  : RG  (Serial reset clock)
    
    # bit 8  : P1  (Parallel clock 1)
    # bit 9  : P2  (Parallel clock 2)
    # bit 10 : P3  (Parallel clock 3)
    # bit 11 : P4  (Parallel clock 4)
    # bit 12 : SPL (ADC trigger ('sample'))
    
    # bit 16 : SHU (Shutter TTL)
    
    # RRRCRRRRPPPPS
    # UDSL123G1234P
    #   T         L

    default_functions = { 0 : 
                          # function 0 : default state
                          # rriClient 2 write 0x100000 0x6bc
                          #
                          fpga.Function(name = "default state",
                                        timelengths = {  0 : 2,  # x10ns
                                                         1 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||
                                        outputs =     {  0 : 0b0000000000000011010111100,
                                                         1 : 0 } ),
                          1 : 
                          # function 1 : shutter function 
                          # currently just keeping shutter open and clocks in position
                          # duration 100 us, repeat for exposure time
                          # cannot have only one timeslice in sequence
                          # rriClient 2 write 0x100010 0x106BC
                          # rriClient 2 write 0x100011 0x106BC
                          # rriClient 2 write 0x200010 10000
                          # rriClient 2 write 0x200011 2
                          # rriClient 2 write 0x200012 0
                          # 
                          fpga.Function(name = "shutter",
                                        timelengths = {  0 : 5000,  # x10ns
                                                         1 : 5000,
                                                         2 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000010000011010111100,
                                                         1 : 0b0000000010000011010111100,
                                                         2 : 0 } ),
                          2 : 
                          # function 2 : line transfer
                          # should be replaced by crossing transfers when REB can handle it
                          # rriClient 2 write 0x100020 0x000006BC 
                          # rriClient 2 write 0x100021 0x00000EBC 
                          # rriClient 2 write 0x100022 0x00000CBC 
                          # rriClient 2 write 0x100023 0x00000DBC 
                          # rriClient 2 write 0x100024 0x000009BC 
                          # rriClient 2 write 0x100025 0x00000BBC 
                          # rriClient 2 write 0x100026 0x000003BC 
                          # rriClient 2 write 0x100027 0x000007BC 
                          # rriClient 2 write 0x100028 0x000006BC 
                          # rriClient 2 write 0x200020 100 
                          # rriClient 2 write 0x200021 1000 
                          # rriClient 2 write 0x200022 1000 
                          # rriClient 2 write 0x200023 1000 
                          # rriClient 2 write 0x200024 1000 
                          # rriClient 2 write 0x200025 1000 
                          # rriClient 2 write 0x200026 1000 
                          # rriClient 2 write 0x200027 1000 
                          # rriClient 2 write 0x200028 1000
                          # rriClient 2 write 0x200029 0
                          fpga.Function(name = "line transfer",
                                        timelengths = {  0 : 100,  # x10ns
                                                         1 : 1000,
                                                         2 : 1000,
                                                         3 : 1000,
                                                         4 : 1000,
                                                         5 : 1000,
                                                         6 : 1000,
                                                         7 : 1000,
                                                         8 : 1000,
                                                         9 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000000000011010111100,
                                                         1 : 0b0000000000000111010111100,
                                                         2 : 0b0000000000000110010111100,
                                                         3 : 0b0000000000000110110111100,
                                                         4 : 0b0000000000000100110111100,
                                                         5 : 0b0000000000000101110111100,
                                                         6 : 0b0000000000000001110111100,
                                                         7 : 0b0000000000000011110111100,
                                                         8 : 0b0000000000000011010111100,
                                                         9 : 0 } ),
                          3 : 
                          # function 3 : pixel read, 2 us
                          # transcribed from Peter Doherty's Geary setup at Harvard
                          # increased overlaps from 50 ns to 80 ns
                          # increased RG up time by 100 ns
                          # delayed ASPIC RST/CL until second slice so RG is actually up
                          # first slice lasts one cycle longer than programmed, last slice two cycles
                          # rriClient 2 write 0x100030 0x6a0
                          # rriClient 2 write 0x100031 0x6ec
                          # rriClient 2 write 0x100032 0x64c
                          # rriClient 2 write 0x100033 0x640
                          # rriClient 2 write 0x100034 0x641
                          # rriClient 2 write 0x100035 0x651
                          # rriClient 2 write 0x100036 0x610
                          # rriClient 2 write 0x100037 0x612
                          # rriClient 2 write 0x100038 0x630
                          # rriClient 2 write 0x100039 0x620
                          # rriClient 2 write 0x10003a 0x1620
                          # rriClient 2 write 0x200030 11
                          # rriClient 2 write 0x200031 18
                          # rriClient 2 write 0x200032 10
                          # rriClient 2 write 0x200033 10
                          # rriClient 2 write 0x200034 42
                          # rriClient 2 write 0x200035 8
                          # rriClient 2 write 0x200036 20
                          # rriClient 2 write 0x200037 50
                          # rriClient 2 write 0x200038 8
                          # rriClient 2 write 0x200039 12
                          # rriClient 2 write 0x20003a 8
                          # rriClient 2 write 0x20003b 0
                          #
                          fpga.Function(name = "read pixel",
                                        timelengths = {  0 : 11,  # x10ns
                                                         1 : 18,
                                                         2 : 10,
                                                         3 : 10,
                                                         4 : 42,
                                                         5 : 8,
                                                         6 : 20,
                                                         7 : 50,
                                                         8 : 8,
                                                         9 : 12,
                                                        10 : 8,
                                                        11 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000000000011010100000,
                                                         1 : 0b0000000000000011011101100,
                                                         2 : 0b0000000000000011001001100,
                                                         3 : 0b0000000000000011001000000,
                                                         4 : 0b0000000000000011001000001,
                                                         5 : 0b0000000000000011001010001,
                                                         6 : 0b0000000000000011000010000,
                                                         7 : 0b0000000000000011000010010,
                                                         8 : 0b0000000000000011000110000,
                                                         9 : 0b0000000000000011000100000,
                                                        10 : 0b0000000000001011000100000,
                                                        11 : 0 } ),
                          4 :
                              # function 4 : pixel transfer, 2 us
                          # function with that replicates acquisition timings without ADC trigger
                          # rriClient 2 write 0x100040 0x6a0
                          # rriClient 2 write 0x100041 0x6ec
                          # rriClient 2 write 0x100042 0x64c
                          # rriClient 2 write 0x100043 0x640
                          # rriClient 2 write 0x100044 0x641
                          # rriClient 2 write 0x100045 0x651
                          # rriClient 2 write 0x100046 0x610
                          # rriClient 2 write 0x100047 0x612
                          # rriClient 2 write 0x100048 0x630
                          # rriClient 2 write 0x100049 0x620
                          # rriClient 2 write 0x10004a 0x620
                          # rriClient 2 write 0x200040 11
                          # rriClient 2 write 0x200041 18
                          # rriClient 2 write 0x200042 10
                          # rriClient 2 write 0x200043 10
                          # rriClient 2 write 0x200044 42
                          # rriClient 2 write 0x200045 8
                          # rriClient 2 write 0x200046 20
                          # rriClient 2 write 0x200047 50
                          # rriClient 2 write 0x200048 8
                          # rriClient 2 write 0x200049 12
                          # rriClient 2 write 0x20004a 8
                          # rriClient 2 write 0x20004b 0
                          #
                          fpga.Function(name = "read pixel (no ADC)",
                                        timelengths = {  0 : 11,  # x10ns
                                                         1 : 18,
                                                         2 : 10,
                                                         3 : 10,
                                                         4 : 42,
                                                         5 : 8,
                                                         6 : 20,
                                                         7 : 50,
                                                         8 : 8,
                                                         9 : 12,
                                                        10 : 8,
                                                        11 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000000000011010100000,
                                                         1 : 0b0000000000000011011101100,
                                                         2 : 0b0000000000000011001001100,
                                                         3 : 0b0000000000000011001000000,
                                                         4 : 0b0000000000000011001000001,
                                                         5 : 0b0000000000000011001010001,
                                                         6 : 0b0000000000000011000010000,
                                                         7 : 0b0000000000000011000010010,
                                                         8 : 0b0000000000000011000110000,
                                                         9 : 0b0000000000000011000100000,
                                                        10 : 0b0000000000000011000100000,
                                                        11 : 0 } ),
                          
                          5 :
                              # function 5 : fast clear line transfer (as fast as can be with current REB)
                          # rriClient 2 write 0x100050 0x000006BC 
                          # rriClient 2 write 0x100051 0x00000CBC 
                          # rriClient 2 write 0x100052 0x000009BC 
                          # rriClient 2 write 0x100053 0x000003BC 
                          # rriClient 2 write 0x100054 0x000006BC 
                          # rriClient 2 write 0x200050 99
                          # rriClient 2 write 0x200051 1000 
                          # rriClient 2 write 0x200052 1000 
                          # rriClient 2 write 0x200053 1000 
                          # rriClient 2 write 0x200054 1000 
                          # rriClient 2 write 0x200055 0 
                          #
                          fpga.Function(name = "fast line transfer",
                                        timelengths = {  0 : 99,  # x10ns
                                                         1 : 1000,
                                                         2 : 1000,
                                                         3 : 1000,
                                                         4 : 1000,
                                                         5 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000000000011010111100,
                                                         1 : 0b0000000000000110010111100,
                                                         2 : 0b0000000000000100110111100,
                                                         3 : 0b0000000000000001110111100,
                                                         4 : 0b0000000000000011010111100,
                                                         5 : 0 }),

                          6 : 
                          # function 6 : fast clear serial transfer (900 ns)
                          # rriClient 2 write 0x100060 0x6ac
                          # rriClient 2 write 0x100061 0x6ec
                          # rriClient 2 write 0x100062 0x64c
                          # rriClient 2 write 0x100063 0x65c
                          # rriClient 2 write 0x100064 0x61c
                          # rriClient 2 write 0x100065 0x63c
                          # rriClient 2 write 0x100066 0x62c
                          # rriClient 2 write 0x200060 0xe
                          # rriClient 2 write 0x200061 0x5
                          # rriClient 2 write 0x200062 0x14
                          # rriClient 2 write 0x200063 0x5
                          # rriClient 2 write 0x200064 0x14
                          # rriClient 2 write 0x200065 0x5
                          # rriClient 2 write 0x200066 0x12
                          # rriClient 2 write 0x200067 0
                          #
                          fpga.Function(name = "fast serial transfer",
                                        timelengths = {  0 : 14,  # x10ns
                                                         1 : 5,
                                                         2 : 20,
                                                         3 : 5,
                                                         4 : 20,
                                                         5 : 5,
                                                         6 : 18,
                                                         7 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||                                 
                                        outputs =     {  0 : 0b0000000000000011010101100,
                                                         1 : 0b0000000000000011011101100,
                                                         2 : 0b0000000000000011001001100,
                                                         3 : 0b0000000000000011001011100,
                                                         4 : 0b0000000000000011000011100,
                                                         5 : 0b0000000000000011000111100,
                                                         6 : 0b0000000000000011000101100,
                                                         7 : 0 } ),
                          
                          7 : 
                          # function 7 : fast clear while shutter is open (900 ns)
                          # rriClient 2 write 0x100070 0x106ac
                          # rriClient 2 write 0x100071 0x106ec
                          # rriClient 2 write 0x100072 0x1064c
                          # rriClient 2 write 0x100073 0x1065c
                          # rriClient 2 write 0x100074 0x1061c
                          # rriClient 2 write 0x100075 0x1063c
                          # rriClient 2 write 0x100076 0x1062c
                          # rriClient 2 write 0x200070 0xe
                          # rriClient 2 write 0x200071 0x5
                          # rriClient 2 write 0x200072 0x14
                          # rriClient 2 write 0x200073 0x5
                          # rriClient 2 write 0x200074 0x14
                          # rriClient 2 write 0x200075 0x5
                          # rriClient 2 write 0x200076 0x12
                          # rriClient 2 write 0x200077 0
                          #
                          fpga.Function(name = "fast serial transfer (open shutter)",
                                        timelengths = {  0 : 14,  # x10ns
                                                         1 : 5,
                                                         2 : 20,
                                                         3 : 5,
                                                         4 : 20,
                                                         5 : 5,
                                                         6 : 18,
                                                         7 : 0 },
                                        #                    
                                        #                      ........S...SPPPPRRRRCRRR
                                        #                      ........H...P4321G321LSDU
                                        #                      ........U...L|||||||||T||
                                        outputs =     {  0 : 0b0000000010000011010101100,
                                                         1 : 0b0000000010000011011101100,
                                                         2 : 0b0000000010000011001001100,
                                                         3 : 0b0000000010000011001011100,
                                                         4 : 0b0000000010000011000011100,
                                                         5 : 0b0000000010000011000111100,
                                                         6 : 0b0000000010000011000101100,
                                                         7 : 0 } ) }

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

    def __init__(self, reb_id = 2, ctrl_host = None, strip_id = 0):
        self.reb_id = reb_id
        self.ctrl_host = ctrl_host
        self.fpga = fpga.FPGA(ctrl_host = self.ctrl_host, 
                              reb_id = self.reb_id)
    	self.strip_id = strip_id

        self.program = None
        self.functions = {}

    # --------------------------------------------------------------------

    def read(self, address, n = 1, check = True):
        """
        Read a FPGA register and return its value.
        if n > 1, returns a list of values as a dictionary.
        """
        return self.fpga.read(address = address, n = n, check = check)

    def write(self, address, value, check = True):
        """
        Write a given value into a FPGA register.
        """
        return self.fpga.write(address = address, value = value, check = check)

    # --------------------------------------------------------------------

    def get_schema(self):
        addr = 0x0
        result = self.read(address = addr)
        if not(result.has_key(addr)):
            raise IOError("Failed to read FPGA memory at address " + str(addr))
        return result[addr]

    schema = property(get_schema, "FPGA address map version")

    # ----------------------------------------------------------

    def get_version(self):
        return self.fpga.get_version()

    version = property(get_version, "FPGA VHDL version")

    # ----------------------------------------------------------

    def get_sci_id(self):
        return self.fpga.get_sci_id()

    sci_id = property(get_sci_id, "SCI's own address")

    # ----------------------------------------------------------

    def get_state(self):
        return self.fpga.get_state()

    state = property(get_state, "FPGA state")

    # ----------------------------------------------------------

    def set_trigger(self, trigger):
        self.fpga.set_trigger(trigger)

    # --------------------------------------------------------------------

    def start_clock(self):
        """
        Start the FPGA internal clock counter.
        """
        self.fpga.start_clock()

    def stop_clock(self):
        """
        Stop the FPGA internal clock counter.
        """
        self.fpga.stop_clock()

    def get_time(self):
        return self.fpga.get_time()

    def set_time(self, t):
        self.fpga.set_time(t)

    time = property(get_time, set_time, 
                    "FPGA current time (internal clock, in 10ns units)")

    # --------------------------------------------------------------------

    def start(self):
        """
        Start the sequencer program.
        """
        self.fpga.start()

    def stop(self):
        """
        Send the command STOP.
        """
        self.fpga.stop()

    def step(self):
        """
        Send the command STEP.
        """
        self.fpga.step()

    # --------------------------------------------------------------------

    def send_function(self, function_id, function):
        """
        Send the function <function> into the FPGA memory 
        at the #function_id slot.
        """
        self.fpga.send_function(function_id, function)
        self.functions[function_id] = function # to keep memory

    def send_functions(self, functions):
        """
        Load all functions from dict <functions> into the FPGA memory.
        """
        self.fpga.send_functions(functions)
        self.functions.update(functions)

    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        return self.fpga.dump_function(function_id)

    def dump_functions(self):
        """
        Dump all functions from the FPGA memory.
        """
        return self.fpga.dump_functions()
        
    # --------------------------------------------------------------------

    def send_program_instruction(self, addr, instr):
        """
        Load the program instruction <instr> at relative address <addr> 
        into the FPGA program memory.
        """
        self.fpga.send_program_instruction(addr, instr)

    def send_program(self, program, clear = True):
        """
        Load the compiled program <program> into the FPGA program memory.
        """
        self.fpga.send_program(program, clear = clear)

    def load_program(self, program = default_program, clear = True):
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
        self.send_program(program, clear = clear)

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

    def send_sequencer(self, seq, clear = True):
        """
        Load the functions and the program at once.
        """
        self.fpga.send_sequencer(seq, clear = clear)

    def dump_sequencer(self):
        """
        Dump the sequencer program and the 16 functions from the FPGA memory.
        """
        return self.fpga.dump_sequencer()

    # --------------------------------------------------------------------

    # def count_subroutine(self, subname, bit, transition = 'on'):
    #     """
    #     Counts how many time bit <bit> is switched on/off 
    #     (depending of <transition> value) when subroutine 
    #     <subname> is called.
    #     Useful to compute the image size.

    #     TO BE WRITTEN (not so simple)

    #     """
    #     pass

    # --------------------------------------------------------------------

    # Not useful anymore
    # def set_image_size(self, size):
    #     """
    #     Set image size (in ADC count).
    #     """
    #     self.fpga.set_image_size(size)

    # --------------------------------------------------------------------

    def get_board_temperatures(self):
        return self.fpga.get_board_temperatures()

    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.fpga.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def set_dacs(self, dacs):
        """
        Sets CS gate or clock voltage DACs, but not both at the same time (for extra safety).
        """

        if "I_OS" in dacs:
            self.fpga.set_current_source(dacs)
        else:
            self.fpga.set_clock_voltages(dacs)

    # --------------------------------------------------------------------

    def get_cabac_config(self): 
        """
        read CABAC configuration.
        """
        return self.fpga.get_cabac_config(self.strip_id)
    
    # --------------------------------------------------------------------

    def set_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
    
        for param in iter(params):
            self.fpga.set_cabac_value(param, params[param])

        self.fpga.set_cabac_config(self.strip_id)
        
        time.sleep(0.5)
        
        self.fpga.get_cabac_config(self.strip_id)

        for param in iter(params):
            self.fpga.check_cabac_value(param, params[param])

    # ----------------------------------------------------------
    
    def get_operating_header(self, headername = "CCDoperating.txt"):
        """
        Fills FITS header for CCD operating conditions
        """
        headerfile = open(headername,'w')
        headerfile.write(self.get_cabac_config())
        headerfile.write(self.fpga.get_clock_voltage())
        headerfile.write(self.fpga.get_current_source())

#need to add power currents and voltages, back substrate value and current (added elsewhere ?)


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
