#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import py.camera.reb1.reb1 as reb1

from driver import Driver

# =======================================================================

class Instrument(Driver):
    # ===================================================================
    # Generic methods (init, open, etc)
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

        if 'reb_id' not in kargs:
            raise ValueError("reb_id is requested")

        if 'host' not in kargs:
            self.host = None

        if 'stripe_id' not in kargs:
            self.stripe_id = 0

        if 'xmlfile' not in kargs:
            raise ValueError("XML sequencer file is requested")

        self.reb = reb1.REB1(reb_id=self.reb_id, ctrl_host=self.host, stripe_id=[self.stripe_id])
        self.reb.xmlfile = self.xmlfile
        self.version = self.reb.fpga.get_version()

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

        if answer is None:
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
        if not connected:
            raise IOError(
                "REB #%d not connected.\n You should run this on the computer connected to the crate." % self.reb_id)

        Driver.register(self, bench)

    def close(self):
        """
        Close the hardware connection.
        """
        pass

    # ===================================================================
    #  Instrument specific methods
    # ===================================================================

    # ----------------------------------------------------------
    # FPGA basic configuration and communication
    # --------------------------------------------------------------------

    def read(self, address, n=1, check=True):
        """
        Read a FPGA register and return its value.
        if n > 1, returns a list of values as a dictionary.
        """
        return self.reb.fpga.read(address=address, n=n, check=check)

    def write(self, address, value, check=True):
        """
        Write a given value into a FPGA register.
        """
        return self.reb.fpga.write(address=address, value=value, check=check)

    def get_state(self):
        return self.reb.fpga.get_state()

    def set_stripe(self, stripe_id=0):
        """
        Set which REB stripe is read out.
        At this level, accepts only one stripe, but the underlying structure is valid for more.
        """
        self.stripe_id = stripe_id
        self.reb.set_stripes([self.stripe_id])

    def update_filetag(self, t):
        """
        Updates the filetag to the FPGA timer.
        :param t: int new numerical tag
        """
        self.reb.update_filetag(t)

    def recover_filetag(self):
        """
        Reads the filetag from the FPGA timer and recovers imgtag if it is in the right format.
        Returns the tag.
        :return: string
        """
        return self.reb.recover_filetag()

    # --------------------------------------------------------------------
    # Sequencer configuration
    # --------------------------------------------------------------------

    def load_sequencer(self, xmlfile=None):
        """
        Load the functions and the program from a file (by default if none given).
        """
        self.reb.load_sequencer(xmlfile)

    def select_subroutine(self, subname, repeat=1):
        """
        Selects the subroutine to be executed by changing the first (main) call in the program.
        """
        self.reb.select_subroutine(subname, repeat)

    def config_sequence(self, subname, exptime=1, shutdelay=100):
        """
        Configure the programmed sequence, including selection, exposure time, and shutter delay.
        """
        self.reb.config_sequence(subname, exptime, shutdelay)

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

    def send_program(self, program, clear=True):
        """
        Load the compiled program <program> into the FPGA program memory.
        """
        self.reb.fpga.send_program(program, clear=clear)

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

    # --------------------------------------------------------------------
    # Running the sequencer
    # --------------------------------------------------------------------

    def execute_sequence(self):
        """
        Executes the currently loaded sequence.
        """
        self.reb.execute_sequence()

    def set_trigger(self, trigger):
        self.reb.fpga.set_trigger(trigger)

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

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        self.reb.wait_end_sequencer()

    def waiting_sequence(self, name="Wait"):
        """
        Lets CCD wait by clearing periodically until keyboard interrupt is sent.
        """
        self.reb.waiting_sequence(name)

    # --------------------------------------------------------------------
    # Operating the board electronics
    # --------------------------------------------------------------------

    def REBpowerup(self):
        """
        Operations after powering the REB
        """
        self.reb.REBpowerup()

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """
        self.reb.CCDpowerup()

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """
        self.reb.CCDshutdown()

    def REBshutdown(self):
        """
        Operations to shut down the REB. With REB1, once the CCD is shut down, this
        is only powering down the power supplies.
        """
        pass

    # --------------------------------------------------------------------

    def get_board_temperatures(self):
        return self.reb.fpga.get_board_temperatures()

    def get_input_voltages_currents(self):
        return self.reb.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def set_clock_voltages(self, dacs):
        """
        Sets clock voltage DACs.
        :param dacs: dict
        """
        self.reb.fpga.set_clock_voltages(dacs)

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

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
        self.reb.send_cabac_config(params)

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        self.reb.cabac_reset()

    # --------------------------------------------------------------------
    # Building FITS frames
    # --------------------------------------------------------------------

    def make_img_name(self):
        """
        Reconstitutes the path for the latest raw file created (does not necessarily exists).
        :return: string
        """
        return self.reb.make_img_name()

    def conv_to_fits(self, imgname, channels=None):
        """
        Creates the fits object from the acquired data.
        If channels is not None but a list, saves the channels in the list (number 0 to 15).
        :param imgname: string
        :return: pyfits.HDUlist
        """
        return self.reb.conv_to_fits(imgname, channels)

    def make_fits_name(self, imgstr):
        """
        Builds a complete FITS file path. imgstr should be the name of the file without the extension.
        :param imgstr: string
        :return: string
        """
        return self.reb.make_fits_name(imgstr)

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
                'CTRL_SYS', 'CTRL_ID', 'FIRMWARE', 'CCD_MANU', 'CCD_TYPE', 'CCD_SERN', 'IMGTYPE',
                'EXPTIME', 'SHUT_DEL', 'CTRLCFG', 'IMAGETAG', 'DETSIZE', 'WIDTH', 'HEIGHT', 'SYSGAIN']

        # comments : meaning of the keys
        comments = {
            'DATE-OBS': 'Date of the observation (image acquisition), UTC',
            'LSST_LAB': 'Which site acquired the data',
            'TSTAND': 'Which Test stand at the site was used',
            'INSTRUME': 'CCD Controller type',
            'CCD_CTRL': 'Duplicates INSTRUME',
            'CTRL_SYS': 'Instrument Software Driver',
            'CTRL_ID': 'CCD Controller Serial Number',
            'FIRMWARE': 'CCD Controller Firmware Version',
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
            'FIRMWARE': self.version,
            'CCD_MANU': 'E2V',
            'CCD_TYPE': 'E2V250',
            'CCD_SERN': '100-00',
            'IMGTYPE': self.reb.seqname,
            'EXPTIME': self.reb.exptime,
            'SHUT_DEL': self.reb.shutdelay,
            'CTRLCFG': self.xmlfile,
            'IMAGETAG': self.reb.imgtag,
            'DETSIZE': self.reb.get_detsize(displayborders=False),
            'WIDTH': self.reb.imgcols,
            'HEIGHT': self.reb.imglines,
            'SYSGAIN': 0.35
        }

        return keys, values, comments

    def get_meta_operating(self):
        """
        More meta data for operating parameters (CABACs, ASPICs when they are added, various REB DACs).
        :return:
        """

        # power supplies measured on board
        header = self.reb.get_input_voltages_currents()
        # cabacs
        header.update_frommeta(self.get_cabac_config())
        # clock rail voltages
        header.update_frommeta(self.reb.fpga.get_clock_voltages())
        # current sources
        header.update_frommeta(self.reb.fpga.get_current_source())

        return header.keys, header.values, header.comments

# TODO: add more meta to put in secondary headers

# needed elsewhere

#def mock_acquire():
    # stuff to put elsewhere for a full acquisition with header
    #primeheader = {}
    #primeheader["TESTTYPE"] = "Test" DARK:FLAT:OBS:PPUMP:QE:SFLAT
    #DATE
    #TEMP_SET	-95.00
#CCDTEMP	-95.12
#MONDIODE	143.12
#MONOWL	550.00
#FILTER	'550LP'
#FILENAME	[Original name of the file]
#exthdu = get_sequencer_hdu(self.reb.fpga)