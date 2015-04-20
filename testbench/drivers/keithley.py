#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Keithley multimeter (through keithley-server and XML-RPC)
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
#   help()                       this information

# current measurement related methods
#   zeroCorrect()                performs zero correct procedure
#   double getCurrent()          the last read value, instrument must be acquiring continuously
#   readContinuous(int)          -1 to stop, 0 to read fastest, other value = delay between reads
#   setRate(double)              sets read rate 0.01 --> 10.0 or 50.0 (if model is 6487)
#   startSequence(int)           begins acquiring a sequence, argument: number of data values to acquire
#   getSequence()                returns the list of read values (double)

# voltage source related methods (only 6487 model)
#   getVoltageRange              returns int 0: 10V 1: 50V 2: 500V
#   setVoltageRange              int argument [0-2]
#   getVoltage                   returns a double, preset output voltage
#   setVoltage                   double argument, [-70.0, 0.0]
#   getCurrentLimit              returns int 0: 25uA, 1: 250uA, 2: 2.5mA and 3: 25mA iff voltage range is 10V
#   setCurrentLimit              int argument [0-2,3]
#   sourceVoltage                int argument 0: stop sourcing, other value sources voltage
#   voltageStatus                returns int 0: not sourcing 1: sourcing

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

        if answer == "":
            return False

        if 'KEITHLEY' not in answer:
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.getModel()


    def register(self):
        Driver.register(self)

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


    def clear(self):
        """
        Clear the instrument status.
        """ 
        # logging.info("Keithley.clear() called.")
        result = self.xmlrpc.clear()
        # logging.info("Keithley.clear() done.")
        return result

    
    # ----------------------- Keithley generic command ------------------

    def send(self, command, timeout = None):
        """
        Send a command through the serial port.
        Read the answer from the serial port.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """

        # logging.info("Keithley.send() called.")
        # logging.info("  command = [%s]" % command)
        answer = self.xmlrpc.send(command, timeout = timeout)
        # logging.info("  answer = [%s]" % answer)
        # logging.info("Keithley.send() done.")
        return answer

    # ----------------------- Keithley identification -------------------

    def get_serial(self):
        """
        Return the identification string of the Keithley.
        """
        # logging.info("Keithley.get_serial() called.")
        serial = self.xmlrpc.get_serial()
        # logging.info("  serial = [%s]" % serial)
        # logging.info("Keithley.get_serial() done.")
        return serial

    # ----------------------- Various methods ---------------------------

    def scroll_text(self, msg):
        """
        Scroll text 'msg' on the Multimeter display.
        For debug purpose only.
        """
        # logging.info("Keithley.scroll_text() called.")
        result = self.xmlrpc.scroll_text(msg)
        # logging.info("Keithley.scroll_text() done.")
        return result


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

    # ===================================================================
