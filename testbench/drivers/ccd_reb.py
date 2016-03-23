#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""

import lsst.camera.reb1.reb1 as reb1
import lsst.camera.wreb.wreb as wreb
import lsst.camera.reb3.reb3 as reb3
from lsst.camera.generic.reb import *
import lsst.camera.generic.rebplus as rebplus

from driver import Driver
import logging
import os.path
import time

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

        if self.hardware == 'REB1':
            self.reb = reb1.REB1(reb_id=self.reb_id, ctrl_host=self.host, stripe_id=[self.stripe])
            self.useCABAC = True
        elif self.hardware == 'WREB1':
            self.reb = wreb.WREB(rriaddress=self.reb_id, ctrl_host=self.host, stripe_id=[self.stripe])
            self.useCABAC = True
            self.reb.useCABACbias = True
        elif self.hardware in ['REB3', 'REB4']:
            self.reb = reb3.REB3(self.bcfile)
            self.useCABAC = False
        else:
            raise ValueError('Unknown type of hardware: %s' % self.hardware)

        # then check FPGA version after connecting
        checkversion = self.reb.fpga.get_version()
        if self.version != checkversion:
            raise ValueError('Wrong version of the FPGA firmware: reading %x instead of %x'
                             % (checkversion, self.version))

        self.reb.xmlfile = self.xmlfile
        self.read_sequencer_file(self.xmlfile)
        self.reb.exptime = self.reb.get_exposure_time()
        
        # CCD and test-related values (for meta)
        self.testID = { 'TESTTYPE': 'TEST', 'IMGTYPE': 'TEST', 'SEQNUM': 0}
        self.sensorID = { 'CCD_MANU': 'NONE', 'CCD_TYPE': 'NONE', 'CCD_SERN': '000-00', 'LSST_NUM': 'NONE'}

        logging.basicConfig(filename='REB-'+ time.strftime('%Y%m%d', time.gmtime()) + '.log',
                            level=logging.DEBUG, format='%(asctime)s: %(message)s')
        # in keithley-server, at this point we deactivate the sys.std<> pipes

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
            answer = self.reb.fpga.read(0x2)[0x2]
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
        self.boardID = self.reb.fpga.get_boardID()
        
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

    def read_sequencer_file(self, xmlfile):
        """
        Reads file to internal REB variable, but does not load it.
        :param xmlfile:
        :return:
        """
        self.reb.read_sequencer_file(xmlfile)

    def load_sequencer(self, xmlfile=None):
        """
        Load the functions and the program from a file (by default if none given).
        """
        self.reb.load_sequencer(xmlfile)
        logging.info("Loaded XML sequencer file %s to REB" % os.path.join(self.reb.xmldir, self.reb.xmlfile))

    def select_subroutine(self, subname, repeat=1):
        """
        Selects the subroutine to be executed by changing the first (main) call in the program.
        """
        self.reb.select_subroutine(subname, repeat)
        logging.info("Selected subroutine %s with repeat %d" % (self.reb.seqname, repeat))

    def config_sequence(self, subname, exptime=0.1, shutdelay=100):
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

    def start_waiting_sequence(self, name="InfiniteWait"):
        """
        Lets CCD wait by clearing infinitely until stop command is sent.
        """
        logging.info("REB: starting wait sequence")
        self.reb.waiting_sequence(name, True)

    def stop_waiting_sequence(self, name=None):
        """
        New: sends the stop command to the infinite loop, and replaces with the named sequence,
        or the memorized sequence if None.
        """
        self.reb.waiting_sequence(name, False)
        logging.info("REB: end wait sequence infinite loop")

    def start_adc_increment(self, offset=0):
        """
        Starts the counter that will increment the ADC convert offset by 10 ns every cycle.
        :param offset: int
        :return:
        """
        if self.hardware == 'REB1':
            logging.info("ADC increment not implemented in this version")
        else:
            logging.info("Starting ADC increment at %d" % offset)
            self.reb.increment(offset)

    def stop_adc_increment(self):
        """
        Stops the counter that increments the ADC convert offset and resets the offset.
        :return:
        """
        if self.hardware == 'REB1':
            logging.info("ADC increment not implemented in this version")
        else:
            logging.info("Stopping ADC increment")
            self.reb.stop_increment()

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
        Reads CABAC configuration.
        """
        if self.useCABAC:
            return self.reb.get_cabac_config()
        else:
            return self.reb.get_biases()

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        Use set_parameter instead if there is no CABAC.
        """
        if self.useCABAC:
            self.reb.send_cabac_config(params)
            logging.info("REB: sent CABAC values")
        else:
            logging.info("REB: attempting to send CABAC values, not in use")

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        if self.useCABAC:
            self.reb.cabac_reset()
            logging.info("REB: sent CABAC resets")
        else:
            logging.info("REB: attempting to send CABAC reset, not in use")

    # --------------------------------------------------------------------

    def config_aspic(self):
        """
        Sets ASPIC into pre-defined configuration with baseline parameters.
        If it is programmable (not REB1 / ASPIC2).
        """
        self.reb.config_aspic()
        logging.info("REB: loaded ASPIC baseline configuration")

    # --------------------------------------------------------------------

    def set_parameter(self, param, value, location=3):
        """
        Generic interface to set any single parameter of the REB, and check the readback if possible.
        Acceptable parameters depend on the REB version.
        Location value can be 3 for top and bottom of the stripe, 2 for top only, 1 for bottom only (applies
        only to CABAC and ASPIC parameters).
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

    def set_window(self, on, precols=0, cols=256, postcols=0, prerows=0, rows=1000, postrows=0):
        """
        Sets to window acquisition and frame size, or goes back to original size.
        Window coordinates are only loaded if pointers are implemented, otherwise they will be loaded from the
        XML file anyway.
        """
        if issubclass(self.reb, rebplus.REBplus):
            if on:
                self.reb.set_window(precols, cols, postcols, prerows, rows, postrows)
            else:
                self.reb.window_sequence(False)

        else:
            self.reb.window_sequence(on)

    def get_amplifier_size(self):
        """
        Gets the dimension of the image data (from a single amplifier). Only read from the REB object, unless
        pointers are implemented.
        :param window:
        :return:
        """
        # Note : still have not found if this is used anywhere

        if issubclass(self.reb, rebplus.REBplus):
            cols = self.reb.get_pointer('ReadCols')
            lines = self.reb.get_pointer('ReadRows')

        else:
            lines = self.reb.imglines
            cols = self.reb.imgcols

        return cols, lines

    def conv_to_fits(self, imgname, channels=None, displayborders=False):
        """
        Creates the fits object from the acquired data.
        If channels is not None but a list, saves the channels in the list (number 0 to 15).
        :param imgname: string
        :param channels: list
        :param displayborders: bool
        :return: pyfits.HDUlist
        """
        return conv_to_fits(imgname, self.reb.imgcols, self.reb.imglines, self.reb.nchannels, channels, displayborders)

    def make_fits_name(self, imgstr, compressed=True):
        """
        Builds a complete FITS file path. imgstr should be the name of the file without the extension.
        :param imgstr: string
        :return: string
        """
        return make_fits_name(self.reb.fitstopdir, imgstr, compressed)

    def set_testtype(self, name):
        """
        Sets the name of the test for the FITS header. Could be used for other things.
        :param name:
        :return:
        """
        self.testID['TESTTYPE'] = name

    def set_imgtype(self, name):
        self.testID['IMGTYPE'] = name

    def set_seqnum(self, num):
        self.testID['SEQNUM'] = num

    def set_sensorID(self, manu, manutype, sernum):
        """
        Stores CCD ID information for header.
        :param manu:
        :param manutype:
        :param sernum:
        :return:
        """
        self.sensorID['CCD_MANU'] = manu
        self.sensorID['CCD_SERN'] = sernum
        self.sensorID['CCD_TYPE'] = manutype
        self.sensorID['LSST_NUM'] = '-'.join([manu, manutype, sernum])

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
        keys = ['ORIGIN', 'DATE-OBS', 'TSTAND', 'INSTRUME', 'CONTROLL',
                'CTRL_SYS', 'CONTNUM', 'FIRMWARE',
                'CCD_MANU', 'CCD_TYPE', 'CCD_SERN', 'LSST_NUM',
                'TESTTYPE', 'IMGTYPE', 'SEQNUM',
                'EXPTIME', 'SHUT_DEL', 'CTRLCFG', 'IMAGETAG', 'CCDGAIN', 'CCDNOISE',
                'BINX', 'BINY', 'HEADVER']

        # comments : meaning of the keys
        comments = {
            'DATE-OBS': 'Date of the observation (image acquisition), UTC',
            'ORIGIN': 'Which site acquired the data',
            'TSTAND': 'Which Test stand at the site was used',
            'INSTRUME': 'CCD Controller type',
            'CONTROLL': 'Duplicates INSTRUME',
            'CTRL_SYS': 'Instrument Software Driver',
            'CONTNUM': 'CCD Controller Serial Number',
            'FIRMWARE': 'CCD Controller Firmware Version',
            'CCD_MANU': 'CCD Manufacturer: E2V, ITL',
            'CCD_TYPE': 'CCD Model Number',
            'CCD_SERN': 'Manufacturer CCD Serial Number',
            'LSST_NUM': 'LSST Assigned CCD Number ',
            'TESTTYPE': 'TEST:DARK:FLAT:OBS:PPUMP:QE:SFLAT',
            'IMGTYPE': 'Image type',
            'SEQNUM': 'Sequence number',
            'EXPTIME': '[s] Exposure Time in seconds',
            'SHUT_DEL': '[ms] Delay between shutter close command and readout',
            'CTRLCFG': 'Controller configuration file',
            'IMAGETAG': 'Image tag',
            'CCDGAIN': 'Estimate of overall system gain in e/DN',
            'CCDNOISE': 'Rough guess at system noise',
            'BINX': 'Binning along X axis',
            'BINY': 'Binning along Y axis',
            'HEADVER': 'Version number of header'
        }

        values = {
            'DATE-OBS': self.reb.tstamp,
            'ORIGIN': 'LPNHE',
            'TSTAND': 'ISO7',
            'INSTRUME': 'LSST',
            'CONTROLL': 'LSST',
            'CTRL_SYS': 'CCD_REB',
            'CONTNUM': self.boardID,
            'FIRMWARE': self.version,
            'CCD_MANU': self.sensorID['CCD_MANU'],
            'CCD_TYPE': self.sensorID['CCD_TYPE'],
            'CCD_SERN': self.sensorID['CCD_SERN'],
            'LSST_NUM': self.sensorID['LSST_NUM'],
            'TESTTYPE': self.testID['TESTTYPE'],
            'IMGTYPE': self.testID['IMGTYPE'],
            'SEQNUM': self.testID['SEQNUM'],
            'EXPTIME': self.reb.exptime,
            'SHUT_DEL': self.reb.shutdelay,
            'CTRLCFG': self.xmlfile,
            'IMAGETAG': self.reb.imgtag,
            'CCDGAIN': 1.0,
            'CCDNOISE': 15.0,
            'BINX': 1,
            'BINY': 1,
            'HEADVER': 1
        }
        # will need to overwrite BINX and BINY if doing actual rebinning
        data = []

        return keys, values, comments, data

    def get_meta_operating(self):
        """
        More meta data for operating parameters (CABACs, ASPICs, various REB DACs).
        :return:
        """
        # in REB3:
        header = self.reb.get_meta_operating()

        return header.keys, header.values, header.comments

    def get_meta_sequencer(self):
        """
        Returns a string table that can be put in a TableHDU (size 73).
        Does not read back from the sequencer (need to update in the object when making changes).
        :return: numpy.array
        """
        return get_sequencer_string(self.reb.seq)
        

