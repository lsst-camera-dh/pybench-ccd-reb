#
# LSST / LPNHE
# Author: Claire Juramy from original by Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import lsst.camera.reb.fpga as fpga

from driver import Driver

# =======================================================================

class Instrument(Driver):

    # ===================================================================
    #  Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)

        # self.identifier = identifier
        # self.host = host
        # self.device = device
        # self.port = port # XML-RPC port

        # if 'host' not in kargs.keys():
        #     raise ValueError("host is requested")

        # if 'devices' not in kargs.keys():
        #     raise ValueError("devices is requested")

        # if 'port' not in kargs.keys():
        #     raise ValueError("port is requested")

        if reb_id not in kargs.keys():
            raise ValueError("reb_id is requested")

        if host not in kargs.keys():
            raise ValueError("reb_id is requested")

        self.reb_id = reb_id
        self.host = host
        self.strip_id = set()  # to be filled with stripe(s) in use

        self.fpga = fpga.FPGA(ctrl_host = self.host, reb_id = self.reb_id)

        self.program = None
        self.functions = {}

    def open(self):
        """
        Open the hardware connection.
        """
        pass

    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        Returns True if the hardware answers, False otherwise.
        """
        answer = self.checkConnection()

        if answer == None:
            return False

        if answer != self.reb_id:
            return False

        return True

    def checkConnection(self):
        """
        Get the REB id from the REB itself.
        Return it or None.
        """
        try:
            answer = self.fpga.read(0x2)
        except IOError:
            answer = None

        return answer

    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("REB #%d not connected.\n You should run this on the computer connected to the crate." % self.reb_id)

        Driver.register(self, bench)

    def close(self):
        """
        Close the hardware connection.
        """
        pass


    # ===================================================================
    #  Instrument specific methods
    # ===================================================================


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
        self.reb.send_function(function_id, function)

    def send_functions(self, functions):
        """
        Load all functions from dict <functions> into the FPGA memory.
        """
        self.reb.send_functions(functions)

    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        return self.reb.dump_function(function_id)

    def dump_functions(self):
        """
        Dump all functions from the FPGA memory.
        """
        return self.reb.dump_functions()

    # --------------------------------------------------------------------

    def send_program_instruction(self, addr, instr):
        """
        Load the program instruction <instr> at relative address <addr>
        into the FPGA program memory.
        """
        self.reb.send_program_instruction(addr, instr)

    def send_program(self, program, clear = True):
        """
        Load the compiled program <program> into the FPGA program memory.
        """
        self.reb.send_program(program, clear = clear)

    def load_program(self, program = default_program, clear = True):
        """
        Load the compiled program <program> into the FPGA program memory.
        The program may also be provided as an uncompiled text string.
        """
        self.reb.send_program(program, clear = clear)

    def dump_program(self):
        """
        Dump the FPGA sequencer program. Return the program.
        """
        return self.reb.dump_program()

    def clear_program(self):
        """
        Clear the FPGA sequencer program memory.
        """
        self.reb.clear_program()

    def run_program(self):
        """
        Trigger the FPGA sequencer program.
        """
        self.reb.start()


    def select_subroutine(self, subname, repeat = 1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        self.reb.select_subroutine(subname, repeat=repeat)


    def run_subroutine(self, subname, repeat = 1):
        """
        Select and run the specified subroutine
        """
        self.reb.run_subroutine(subname, repeat = repeat)

    # --------------------------------------------------------------------

    def send_sequencer(self, seq, clear = True):
        """
        Load the functions and the program at once.
        """
        self.reb.send_sequencer(seq, clear = clear)

    def dump_sequencer(self):
        """
        Dump the sequencer program and the 16 functions from the FPGA memory.
        """
        return self.reb.dump_sequencer()

    # --------------------------------------------------------------------

    def set_strip(self, strip_id=0):
        """
        Set which REB strip is read out. For now, does not accept more than one strip.
        """
        self.reb.set_strip(strip_id)

    # --------------------------------------------------------------------

    def get_board_temperatures(self):
        return self.reb.get_board_temperatures()

    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.reb.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def set_dacs(self, dacs):
        """
        Sets CS gate or clock voltage DACs, but not both at the same time (for extra safety).
        """
        self.reb.set_dacs(dacs)

    # --------------------------------------------------------------------

    def get_cabac_config(self):
        """
        read CABAC configuration.
        """
        return self.reb.get_cabac_config()

    # --------------------------------------------------------------------

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
        self.reb.send_cabac_config(params)

    # --------------------------------------------------------------------

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        self.reb.reset_cabac()


    # ===================================================================
    #  Meta data / state of the instrument
    # ===================================================================


    def get_meta(self):
        """
        Returns meta data describing the current state
        of the instrument.
        Useful to fill the FITS headers.
        """

        # keys : specify the key order
        keys = ['MODEL',
                'DRIVER']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver'
            }

        values = {
            'MODEL'  : self.get_serial(),
            'DRIVER' : 'keithley-server / keithley'
            }

        return keys, values, comments

