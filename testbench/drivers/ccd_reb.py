#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import lsst.camera.reb1.reb1 as reb1
import lsst.camera.wreb.wreb as wreb
from lsst.camera.generic.reb import get_sequencer_string

from driver import Driver
import logging
import os.path
import subprocess

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

        if 'stripe' not in kargs:
            self.stripe = 0

        if 'xmlfile' not in kargs:
            raise ValueError("XML sequencer file is requested")

        if identifier == 'reb':
            self.reb = reb1.REB1(reb_id=self.reb_id, ctrl_host=self.host, stripe_id=[self.stripe])
        else:
            self.reb = wreb.WREB(rriaddress=self.reb_id, ctrl_host=self.host, stripe_id=[self.stripe])
        self.reb.xmlfile = self.xmlfile
        self.version = self.reb.fpga.get_version()
        self.testtype = 'TEST'

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

        return answer[0x2]

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
        self.stripe = stripe_id
        self.reb.set_stripes([self.stripe])

    def update_filetag(self):
        """
        Updates the filetag from the current time to the FPGA timer.
        """
        self.reb.update_filetag()

    # --------------------------------------------------------------------
    # Sequencer configuration
    # --------------------------------------------------------------------

    def load_sequencer(self, xmlfile=None):
        """
        Load the functions and the program from a file (by default if none given).
        """
        self.reb.load_sequencer(xmlfile)
        logging.info("Loaded XML sequencer file %s" % os.path.join(self.reb.xmldir, self.reb.xmlfile))

    def select_subroutine(self, subname, repeat=1):
        """
        Selects the subroutine to be executed by changing the first (main) call in the program.
        """
        self.reb.select_subroutine(subname, repeat)
        logging.info("Selected subroutine %s with repeat %d" % (self.reb.seqname, repeat))

    def config_sequence(self, subname, exptime=1, shutdelay=100):
        """
        Configure the programmed sequence, including selection, exposure time, and shutter delay.
        """
        self.reb.config_sequence(subname, exptime, shutdelay)
        logging.info("Configured subroutine %s with exposure time %f and shutter delay %f"
                     % (self.reb.seqname, self.reb.exptime, self.reb.shutdelay))

    # --------------------------------------------------------------------

    # For send/dump functions/program : if you want them, go get them in self.reb.fpga
    # Just remember to call self.wait_end_sequencer() first.

    # --------------------------------------------------------------------
    # Running the sequencer
    # --------------------------------------------------------------------

    def execute_sequence(self):
        """
        Executes the currently loaded sequence.
        """
        self.reb.execute_sequence()
        logging.info("REB: sent execute sequence %s to FPGA" % self.reb.seqname)

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

    def start_waiting_sequence(self, name="Wait"):
        """
        Launches a CCD waiting sequence as a subprocess.
        """
        logging.info("REB: starting wait sequence subprocess")
        self.reb.config_sequence(name, 0)
        command = '/home/lsst/lsst/py/testbench/scripts/ccd/repeat_sequence.sh'
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc

    def stop_waiting_sequence(self, proc):
        """
        Lets CCD wait by clearing periodically until keyboard interrupt is sent.
        """
        proc.terminate()
        logging.info("REB: end wait sequence subprocess")

    def start_adc_increment(self, offset=0):
        """
        Starts the counter that will increment the ADC convert offset by 10 ns every cycle.
        :param offset: int
        :return:
        """
        if self.identifier == 'wreb':
            logging.info("Starting ADC increment at %d" % offset)
            self.reb.fpga.increment(offset)
        else:
            logging.info("ADC increment not implemented in this version")

    def stop_adc_increment(self):
        """
        Stops the counter that increments the ADC convert offset and resets the offset.
        :return:
        """
        if self.identifier == 'wreb':
            logging.info("Stopping ADC increment")
            self.reb.fpga.stop_increment()
        else:
            logging.info("ADC increment not implemented in this version")

    # --------------------------------------------------------------------
    # Operating the board electronics
    # --------------------------------------------------------------------

    def REBpowerup(self):
        """
        Operations after powering the REB
        """
        logging.info("Starting to initialize the REB")
        self.reb.REBpowerup()
        logging.info("Initialized the REB")

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """
        logging.info("Starting to power up the CCD on REB")
        self.reb.CCDpowerup()
        logging.info("Powering up the CCD is done on REB")

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """
        logging.info("Starting to shut down the CCD on REB")
        self.reb.CCDshutdown()
        logging.info("CCD shut down sequence is done on REB")

    def REBshutdown(self):
        """
        Operations to shut down the REB. With REB1, once the CCD is shut down, this
        would be only powering down the power supplies. For WREB, this is where we should
        power down CABAC safely (clock rails and low voltage supplies).
        """
        logging.info("Starting to shut down the REB")
        self.reb.REBshutdown()
        logging.info("REB shut down sequence is done")

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
        Beware: clock rail names depend on REB version.
        """
        self.reb.fpga.set_clock_voltages(dacs)
        logging.info("Setting clock voltages")

    def set_current_source(self, dac):
        """
        Sets CS gate DACs.
        :param dac: int
        """
        self.reb.fpga.set_current_source(dac)
        logging.info("Setting current source DACs to %d" % dac)

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
        logging.info("REB: sent CABAC values")

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        self.reb.cabac_reset()
        logging.info("REB: sent CABAC resets")

    # --------------------------------------------------------------------

    def set_parameter(self, param, value, location=3):
        """
        Generic interface to set any single parameter of the REB, and check the readback if possible.
        Acceptable parameters depend on the REB version.
        Location value can be 3 for top and bottom of the stripe, 2 for top only, 1 for bottom only.
        It applies only to CABAC and ASPIC parameters.
        :param param: string
        :param value:
        :param location: int
        """
        self.reb.set_parameter(param, value, self.stripe, location)
        logging.info("Set REB parameter %s to %s at location %d" % (param, repr(value), location))

    # --------------------------------------------------------------------
    # Building FITS frames
    # --------------------------------------------------------------------

    def make_img_name(self):
        """
        Reconstitutes the path for the latest raw file created (does not necessarily exists).
        :return: string
        """
        return self.reb.make_img_name()


    def set_amplifier_size(self, cols, lines):
        """
        Sets the dimensions of the image. This affects how the image is reconstituted, not the sequencer (yet).
        :param cols: int
        :param lines: int
        :return:
        """
        self.reb.imgcols = cols
        self.reb.imglines = lines

    def conv_to_fits(self, imgname, channels=None, displayborders=False):
        """
        Creates the fits object from the acquired data.
        If channels is not None but a list, saves the channels in the list (number 0 to 15).
        :param imgname: string
        :param channels: list
        :param displayborders: bool
        :return: pyfits.HDUlist
        """
        return self.reb.conv_to_fits(imgname, channels, displayborders)

    def make_fits_name(self, imgstr):
        """
        Builds a complete FITS file path. imgstr should be the name of the file without the extension.
        :param imgstr: string
        :return: string
        """
        return self.reb.make_fits_name(imgstr)

    def set_testtype(self, name):
        """
        Sets the name of the test for the FITS header. Could be used for other things.
        :param name:
        :return:
        """
        self.testtype = name

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
                'CTRL_SYS', 'CTRL_ID', 'FIRMWARE', 'CCD_MANU', 'CCD_TYPE', 'CCD_SERN', 'TESTTYPE', 'IMGTYPE',
                'EXPTIME', 'SHUT_DEL', 'CTRLCFG', 'IMAGETAG', 'DETSIZE', 'WIDTH', 'HEIGHT', 'SYSGAIN']

        # comments : meaning of the keys
        comments = {
            'DATE-OBS': 'Date of the observation (image acquisition), UTC',
            'LSST_LAB': 'Which site acquired the data',
            'TSTAND': 'Which Test stand at the site was used',
            'INSTRUME': 'Camera',
            'CCD_CTRL': 'CCD Controller type',
            'CTRL_SYS': 'Instrument Software Driver',
            'CTRL_ID': 'CCD Controller Serial Number',
            'FIRMWARE': 'CCD Controller Firmware Version',
            'CCD_MANU': 'CCD Manufacturer: E2V, ITL',
            'CCD_TYPE': 'CCD Model Number',
            'CCD_SERN': 'LSST Assigned CCD Number ',
            'TESTTYPE': 'TEST:DARK:FLAT:OBS:PPUMP:QE:SFLAT',
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
            'INSTRUME': 'LSST',
            'CCD_CTRL': self.identifier.upper(),
            'CTRL_SYS': 'CCD_REB',
            'CTRL_ID': self.reb_id,
            'FIRMWARE': self.version,
            'CCD_MANU': 'E2V',
            'CCD_TYPE': 'E2V250',
            'CCD_SERN': '100-00',
            'TESTTYPE': self.testtype,
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
        header.update(self.get_cabac_config())
        # clock rail voltages and current source
        header.update(self.reb.fpga.get_dacs())

        return header.keys, header.values, header.comments

    def get_meta_sequencer(self):
        """
        Returns a string table that can be put in a TableHDU (size 73).
        Does not read back from the sequencer (need to update in the object when making changes).
        :return: numpy.array
        """
        return get_sequencer_string(self.reb.seq)
