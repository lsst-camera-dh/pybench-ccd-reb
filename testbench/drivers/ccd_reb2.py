#
# LSST / LPNHE
# Author: Claire Juramy from original by Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import fpga0 as fpga
import rebxml
import time
import string
from driver import Driver

# =======================================================================

class Instrument(Driver):

    xmlfile = "sequencer-wreb.xml"
    rawimgdir = "/home/lsst/test_images"
    fitstopdir = "/home/lsst/test_frames"
    nchannels = 16
    imgtag = 0
    # to be loaded from XML later
    imglines = 2020
    imgcols = 550
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
    min_exposure = int(0.1 / exposure_unit)  # minimal shutter opening time (not used for darks)

    # ===================================================================
    #  Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)

        if "reb_id" not in kargs.keys():
            raise ValueError("reb_id is requested")

        if "host" not in kargs.keys():
            kargs["host"] = None

        self.fpga = fpga.FPGA(ctrl_host=kargs["host"], reb_id=kargs["reb_id"])
        self.set_stripe(0)  # stripe in use

        self.seq = None

        self.recover_filetag()

    def open(self):
        """
        Open the hardware connection.
        """
        print("Remember to launch imageClient in %s" % self.rawimgdir)

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


    # --------------------------------------------------------------------

    def set_stripe(self, strip_id=0):
        """
        Set which REB stripe is read out. For this bench, does not accept more than one stripe.
        """
        if strip_id not in [0, 1, 2]:
            raise ValueError("Incorrect stripe number: %d" % strip_id)

        self.stripe = strip_id
        self.fpga.write(0x400007, 1 << strip_id)

    # --------------------------------------------------------------------
    def get_exposure_time(self, darktime=False):
        """
        Gets the exposure time from the subroutines in memory.
        (input in seconds). If darktime is set to true, gives the dark 'exposure' time instead.
        :param darktime: boolean
        """

        # look up address of exposure subroutine
        # then get current instruction
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            instruction = self.seq.program.instructions[darkadd]
        else:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            instruction = self.seq.program.instructions[exposureadd]
        iter = instruction.repeat

        return float(iter)*self.exposure_unit  # in seconds

    def set_exposure_time(self, exptime, lighttime=True, darktime=True):
        """
        Modifies exposure subroutines to last the given exposure time
        (input in seconds). By default both exposures with shutter open
        and closed are modified, use optional parameters to preserve one
        or the other.
        :param exptime:
        :param lighttime:
        :param darktime:
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        if lighttime:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            newinstruction = self.seq.program.instructions[exposureadd]
            newinstruction.repeat = int(max(newiter, self.min_exposure))  # This does rewrite the seq.program too
            self.fpga.send_program_instruction(exposureadd, newinstruction)
        #same for dark subroutine
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            newinstruction = self.seq.program.instructions[darkadd]
            newinstruction.repeat = int(max(newiter, 1))  # must not be 0 or sequencer gets stuck
            self.fpga.send_program_instruction(darkadd, newinstruction)

    def load_sequencer(self, xmlfile = None):
        """
        Loads all sequencer content.
        :return:
        """
        if xmlfile:
            self.xmlfile = xmlfile

        self.seq = rebxml.fromxmlfile(self.xmlfile)  # use self.seq.program to track addresses
        self.fpga.send_sequencer(self.seq)
        try:
            self.exptime = self.get_exposure_time()
        except:
            print("Warning: could not find exposure subroutine in %s" % xmlfile)

    def select_subroutine(self, subname, repeat = 1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.seq.program == None:
            raise ValueError("No program with identified subroutines yet.")

        if not(self.seq.program.subroutines.has_key(subname)):
            raise ValueError("No subroutine '%s' in the FPGA program." % subname)

        first_instr = fpga.Instruction(
            opcode = fpga.Instruction.OP_JumpToSubroutine,
            address = self.seq.program.subroutines[subname],
            repeat = repeat)

       # load it at the very beginning of the program (rel addr 0x0)
        self.fpga.send_program_instruction(0x0, first_instr)
        self.seq.program.instructions[0x0] = first_instr # to keep it in sync

    def recover_filetag(self):
        """
        Reads the filetag from the FPGA timer and recovers imgtag if it is in the right format.
        Returns the tag.
        :return: string
        """
        t = self.fpga.get_time()
        tagstr = '0x%016x' % t
        todaystr = time.strftime('%Y%m%d', time.gmtime())
        if string.find(tagstr, todaystr) > -1:
            self.imgtag = int(tagstr[-5:], base=10)

        return tagstr

    def update_filetag(self, t):
        """
        Updates the filetag to the FPGA timer.
        :param t: int new numerical tag
        :return:
        """
        self.imgtag = t
        today = time.gmtime()
        tagstr = time.strftime('%Y%m%d', today)+'%05d' % t
        hextag = int(tagstr,16)
        self.fpga.set_time(hextag)

    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.fpga.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def set_current_source(self, value_int):
        """
        Sets CS gate DACs.
        """
        self.fpga.set_current_source(value_int, self.stripe)

    # --------------------------------------------------------------------

    def set_clocks(self, dacs):
        """
        Sets clock rail DACs from voltage values.
        :param dacs: dict
        """
        self.fpga.set_clock_voltages(dacs)

    # --------------------------------------------------------------------

    def get_cabac_config(self):
        """
        read CABAC configuration.
        """
        self.fpga.get_cabac_config(self.stripe)

    # --------------------------------------------------------------------

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
        for param in iter(params):
            self.fpga.set_cabac_value(param, params[param])

        self.fpga.send_cabac_config(self.stripe)

        time.sleep(0.1)

        self.fpga.get_cabac_config(self.stripe)

        for param in iter(params):
            self.fpga.check_cabac_value(param, params[param])

    # --------------------------------------------------------------------

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        self.fpga.reset_cabac(self.stripe)

        time.sleep(0.1)

        self.fpga.get_cabac_config(self.stripe)



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
        fitsheader = self.get_cabac_config()
        fitsheader.update(self.fpga.get_clock_voltages())
        fitsheader.update(self.fpga.get_current_source())

        return keys, values, comments

