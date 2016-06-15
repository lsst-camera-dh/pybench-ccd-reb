#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Keithley multimeter 6514 (through keithley app on remote computer and XML-RPC)
"""

# XML-RPC interface:

# common methods
#   [rc,string] connect()        rc=0 error, rc=1 OK, rc=2 warn, port already opened
#   void close()                 
#   string getModel()            returns the instrument's model or an empty string if no connection
#   int status()                 returns the instrument status (amps.):
#                                   0=not reading, 1=not connected, 2=acquiring continuous,
#                                   3=acquiring  a sequence
#   void setVerbose(bool)        puts software in verbose mode
#   void recordData(String)      records data (amps.) in String file if String is not empty, otherwise stops recording
#   void writeComment(String)    adds String to the header of the record file
#   help()                       this information (for 6487 model in fact)

# current measurement related methods
#   zeroCorrect()                performs zero correct procedure
#   setCurrentRange()            int argument [0-2]
#   double getCurrent()          the last read value, instrument must be acquiring continuously
#   readContinuous(int)          -1 to stop, 0 to read fastest, other value = delay between reads
#   setRate(double)              sets read rate 0.01 --> 10.0 or 50.0 (if model is 6487)
#   startSequence(int)           begins acquiring a sequence, argument: number of data values to acquire
#   getSequence()                returns the list of read values (double)

# voltage measurement related methods
#   zeroCorrectVolts()           performs zero correct procedure for volt measurements
#   selectVolts                  int argument [0-2]: selects DC volt measurement and sets the range
#   readVoltage                  instrument acquires a value
#   retrieveVoltage              retrieves last acquired value from instrument

import time

from driver import Driver

import xmlrpclib

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

        if 'host' not in kargs.keys():
            raise ValueError("host is requested")

        if 'devices' not in kargs.keys():
            raise ValueError("devices is requested")

        if 'port' not in kargs.keys():
            raise ValueError("port is requested")

        self.xmlrpc = xmlrpclib.ServerProxy("http://%s:%d/" % 
                                            (self.host, self.port))
        self.v1 = 0
        self.v2 = 0
        self.rangeV = 0  # for auto

    def open(self):
        """
        Open the hardware connection.
        """
        self.xmlrpc.connect()


    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        Returns True if the hardware answers, False otherwise.
        """
        answer = self.checkConnection()

        if answer != '6514':
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.get_serial()


    def register(self, bench):
        Driver.register(self, bench)

        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("Keithley Multimeter not connected.")


    def close(self):
        """
        Close the hardware connection.
        """
        self.xmlrpc.close()
        # TODO: Check errors


    # ===================================================================
    #  Instrument specific methods
    # ===================================================================


    def status(self):
        """
        Return the status of the system.
        """
        return self.xmlrpc.status()

    # --------------------------------------------------------------

    def reset(self):
        """
        Reset the instrument to the factory default settings
        (with the exception of all remote interface settings).
        """
        # logging.info("Keithley.reset() called.")
        result = self.xmlrpc.reset()
        # logging.info("Keithley.reset() done.")
        return result

    # ----------------------- Keithley identification -------------------

    def get_serial(self):
        """
        Return the identification string of the Keithley.
        """

        serial = self.xmlrpc.getModel()

        return serial

    # ----------------------- Various methods ---------------------------

    def setup(self, rangevolts):
        """
        Does zero correct and sets the voltage range.
        :param r:
        :return:
        """
        self.xmlrpc.selectVolts(rangevolts)  # TODO: check if and how it works
        self.rangeV = rangevolts
        self.xmlrpc.zeroCorrectVolts()  # does it only if not done already

    def get_voltage(self):
        """
        Gets a single voltage readout.
        :return:
        """
        self.xmlrpc.readVoltage()
        time.sleep(0.2)

        return self.xmlrpc.retrieveVoltage()

    def get_voltage_median(self, n=10, verbose=False):
        """
        Gets n voltage readouts and return the median.
        :return:
        """
        volts = []
        for i in range(n):
            self.xmlrpc.readVoltage()
            time.sleep(0.5)
            v = self.xmlrpc.retrieveVoltage()
            volts.append(v)
            if verbose:
                print v
            
        return sorted(volts)[n/2]

    # ===================================================================
    # PRE/POST exposure hooks
    # ===================================================================

    def pre_exposure(self, exptime):
        self.v1 = self.get_voltage_median(5)

    def post_exposure(self):
        self.v2 = self.get_voltage_median(5)

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
                'DRIVER',
                'RANGE',
                'PREEXP',
                'POSTEXP']

        # TODO: check ranges
        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver',
            'RANGE'  : 'Instrument range: 0:Auto, 1:2V, 2:20V',
            'PREEXP' : '[V] measurement before exposure',
            'POSTEXP': '[V] measurement after exposure'
        }

        values = {
            'MODEL'  : self.get_serial()[26:36],
            'DRIVER' : 'keithley_volt',
            'RANGE'  : self.rangeV,
            'PREEXP' : self.v1,
            'POSTEXP': self.v2
            }

        data = []

        return keys, values, comments, data

    # ===================================================================
    
