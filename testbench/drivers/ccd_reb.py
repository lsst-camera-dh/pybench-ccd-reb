#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import lsst.camera.reb1.reb1 as reb

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
        self.stripe_id = 0 ## To change !!

        self.reb = reb.REB(reb_id = self.reb_id, 
                           ctrl_host = self.host, 
                           strip_id = self.stripe_id)

        # exporting the REB functions?

        # self.read          = self.reb.read
        # self.write         = self.reb.write
        # self.get_schema    = self.reb.get_schema
        # self.get_version   = self.reb.get_version
        # self.get_sci_id    = self.reb.get_sci_id
        # self.get_state     = self.reb.get_state
        # self.set_trigger   = self.reb.set_trigger



    def open(self):
        """
        Open the hardware connection.
        """
        print("Remember to launch imageClient in %s" % self.reb.rawimgdir)


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
            answer = self.reb.fpga.read(0x2)
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
        return self.reb.fpga.read(address = address, n = n, check = check)

    def write(self, address, value, check = True):
        """
        Write a given value into a FPGA register.
        """
        return self.reb.fpga.write(address = address, value = value, check = check)

    def get_state(self):
        return self.reb.fpga.get_state()

   # ----------------------------------------------------------

    def set_trigger(self, trigger):
        self.reb.fpga.set_trigger(trigger)

    # --------------------------------------------------------------------

    def start_clock(self):
        """
        Start the FPGA internal clock counter.
        """
        self.reb.fpga.start_clock()

    def stop_clock(self):
        """
        Stop the FPGA internal clock counter.
        """
        self.reb.fpga.stop_clock()

    def get_time(self):
        return self.reb.fpga.get_time()

    def set_time(self, t):
        self.reb.fpga.set_time(t)

    # --------------------------------------------------------------------

    def execute_sequence(self):
        """
        Start the sequencer program.
        """
        self.reb.execute_sequence()

    def stop(self):
        """
        Send the command STOP.
        """
        self.reb.fpga.stop()

    def step(self):
        """
        Send the command STEP.
        """
        self.reb.fpga.step()

    # --------------------------------------------------------------------

    def send_function(self, function_id, function):
        """
        Send the function <function> into the FPGA memory 
        at the #function_id slot.
        """
        self.reb.fpga.send_function(function_id, function)

    def send_functions(self, functions):
        """
        Load all functions from dict <functions> into the FPGA memory.
        """
        self.reb.fpga.send_functions(functions)

    def dump_function(self, function_id):
        """
        Dump the function #function_id from the FPGA memory.
        """
        return self.reb.fpga.dump_function(function_id)

    def dump_functions(self):
        """
        Dump all functions from the FPGA memory.
        NOTE: Stop doing that.
        """
        return self.reb.fpga.dump_functions()
        
    # --------------------------------------------------------------------

    def send_program_instruction(self, addr, instr):
        """
        Load the program instruction <instr> at relative address <addr> 
        into the FPGA program memory.
        """
        self.reb.fpga.send_program_instruction(addr, instr)

    def send_program(self, program, clear = True):
        """
        Load the compiled program <program> into the FPGA program memory.
        """
        self.reb.fpga.send_program(program, clear = clear)

    def load_program(self, program = default_program, clear = True):
        """
        Load the compiled program <program> into the FPGA program memory.
        The program may also be provided as an uncompiled text string.
        """
        self.reb.fpga.send_program(program, clear = clear)

    def dump_program(self):
        """
        Dump the FPGA sequencer program. Return the program.
        """
        return self.reb.fpga.dump_program()

    def clear_program(self):
        """
        Clear the FPGA sequencer program memory.
        """
        self.reb.fpga.clear_program()

    def config_sequence(self, subname, exptime=1, shutdelay=100):
        """
        Configure the programmed sequence.
        """
        self.reb.config_sequence(subname, exptime, shutdelay)

    # --------------------------------------------------------------------

    def load_sequencer(self, xmlfile=None):
        """
        Load the functions and the program from a file (by default if none given).
        """
        self.reb.load_sequencer(self, xmlfile)


    # --------------------------------------------------------------------

    def set_stripe(self, stripe_id=0):
        """
        Set which REB strip is read out. For now, does not accept more than one strip.
        """
        self.reb.set_stripe(stripe_id)


    # --------------------------------------------------------------------

    def get_board_temperatures(self):
        return self.reb.fpga.get_board_temperatures()

    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.reb.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def set_clock_voltages(self, dacs):
        """
        Sets clock voltage DACs.
        :param dacs: dict
        """
        self.reb.fpga.set_clock_voltages(dacs)

    # --------------------------------------------------------------------

    def set_current_source(self, dac):
        """
        Sets CS gate DACs.
        :param dac: int
        """
        self.reb.fpga.set_current_source(dac)
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
        self.reb.cabac_reset()


#TODO: add rest of the function in reb1

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
        keys = ['DATE-OBS', 'LSST_LAB', 'TSTAND', 'INSTRUME', 'CCD_CTRL',
            'CTRL_SYS', 'CTRL_ID', 'CCD_MANU', 'CCD_TYPE', 'CCD_SERN', 'IMGTYPE',
            'EXPTIME', 'SHUT_DEL', 'CTRLCFG', 'IMAGETAG', 'DETSIZE', 'WIDTH', 'HEIGHT', 'SYSGAIN']

        # comments : meaning of the keys
        comments = {
            'DATE-OBS': 'Date of the observation (image acquisition), UTC',
            'LSST_LAB': 'Which site acquired the data',
            'TSTAND': 'Which Test stand at the site was used',
            'INSTRUME': 'CCD Controller type',
            'CCD_CTRL': 'Duplicates INSTRUME',
            'CTRL_SYS': 'Instrument software driver',
            'CTRL_ID': 'CCD Controller Serial Number',
            'CCD_MANU': 'CCD Manufacturer: E2V, ITL',
            'CCD_TYPE': 'CCD Model Number',
            'CCD_SERN': 'LSST Assigned CCD Number ',
            'IMGTYPE': 'Image type',
            'EXPTIME': 'Exposure Time in Seconds',
            'SHUT_DEL': 'Delay between shutter close command and readout in ms',
            'CTRLCFG': 'Sequencer XML file',
            'IMAGETAG': 'Image tag',
            'DETSIZE': 'NOAO MOSAIC keywords',
            'WIDTH': 'CCD columns per channel',
            'HEIGHT': 'CCD lines per channel',
            'SYSGAIN': 'Rough guess at overall system gain in e/DN'
        }

        values = {
            'DATE-OBS': self.reb.tstamp,
            'LSST_LAB': 'LPNHE',
            'TSTAND': 'ISO7',
            'INSTRUME': 'REB1',
            'CCD_CTRL': 'REB1',
            'CTRL_SYS': 'PYREB',
            'CTRL_ID': 2,
            'CCD_MANU': 'E2V',
            'CCD_TYPE': 'E2V250',
            'CCD_SERN': '100-00',
            'IMGTYPE': self.reb.name,
            'EXPTIME': self.reb.exptime,
            'SHUT_DEL': self.reb.shutdelay,
            'CTRLCFG': self.reb.xmlfile,
            'IMAGETAG': self.reb.imgtag,
            'DETSIZE': '[0:%d,0:%d]' % (self.reb.imgcols * self.reb.nchannels / 2, 2 * self.reb.imglines),
            'WIDTH': self.reb.imgcols,
            'HEIGHT': self.reb.imglines,
            'SYSGAIN': 0.7
        }
        fitsheader = self.get_cabac_config()
        fitsheader.update(self.reb.fpga.get_clock_voltages())
        fitsheader.update(self.reb.fpga.get_current_source())

        return keys, values, comments

#TODO: add more meta to put in secondary headers
