#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Keithley multimeter 
(through keithley-server and XML-RPC).
"""

# XML-RPC interface:
#
# # General Control Functions 
# server.register_function(keithley.status,       "status")
# server.register_function(keithley.open,         "open")
# server.register_function(keithley.close,        "close")
# server.register_function(keithley.reset,        "reset")
# server.register_function(keithley.clear,        "clear")
# server.register_function(keithley.get_serial,   "get_serial")
# server.register_function(keithley.get_serial,   "checkConnection")

# # Keithley generic command
# server.register_function(keithley.send,         "send")
# server.register_function(keithley.get_error_status,  "get_error_status")

# # misc 
# server.register_function(keithley.scroll_text,  "scroll_text")
# server.register_function(server_quit,           "quit")

# # for remote introspection (tab completion with ipython)
# server.register_function(keithley._listMethods, "__dir__")
# server.register_function(keithley._listMethods, "system.listMethods")
# server.register_function(keithley._listMethods,  "trait_names")
# server.register_function(keithley._listMethods,  "_getAttributeNames")
# # TODO: implement: system.methodSignature
# server.register_function(keithley._methodHelp,  "system.methodHelp")

from driver import Driver

import xmlrpclib
import logging

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
        self.xmlrpc.open()


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
        return self.xmlrpc.checkConnection()


    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("Keithley Multimeter not connected.")

        Driver.register(self, bench)


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
        logging.info("Keithley.reset() called.")
        result = self.xmlrpc.reset()
        logging.info("Keithley.reset() done.")
        return result


    def clear(self):
        """
        Clear the instrument status.
        """ 
        logging.info("Keithley.clear() called.")
        result = self.xmlrpc.clear()
        logging.info("Keithley.clear() done.")
        return result

    
    # ----------------------- Keithley generic command ------------------

    def send(self, command, timeout = 1.0):
        """
        Send a command through the serial port.
        Read the answer from the serial port.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """

        logging.info("Keithley.send() called.")
        logging.info("  command = [%s]" % command)
        answer = self.xmlrpc.send(command, timeout)
        logging.info("  answer = [%s]" % answer)
        logging.info("Keithley.send() done.")
        esr = self.xmlrpc.get_error_status()
        if esr != 0:
            logging.error("Keithley command [%s] failed: error code ESR = %d." 
                          % (command, esr))
            raise IOError("Keithley command [%s] failed: error code ESR = %d." 
                          % (command, esr))
        return answer

    # ----------------------- Keithley identification -------------------

    def get_serial(self):
        """
        Return the identification string of the Keithley.
        """
        logging.info("Keithley.get_serial() called.")
        serial = self.xmlrpc.get_serial()
        logging.info("  serial = [%s]" % serial)
        logging.info("Keithley.get_serial() done.")
        return serial

    # ----------------------- Various methods ---------------------------

    def scroll_text(self, msg):
        """
        Scroll text 'msg' on the Multimeter display.
        For debug purpose only.
        """
        logging.info("Keithley.scroll_text() called.")
        result = self.xmlrpc.scroll_text(msg)
        logging.info("Keithley.scroll_text() done.")
        return result


    # ----------------------- Higher level methods ----------------------

    def setup_current_measurements(self, current_range):
        """
        Reset the Keithley and set it up for current measurements,
        using the specified current range (float).
        Useful when using photodiodes (DKD, NIST, etc).
        """
        logging.info("Keithley.setup_current_measurements() called.")
        self.send("*RST")
        self.send("SYST:ZCH ON")
        self.send("FUNC 'CURR:DC'")
        self.send("CURR:RANG %.2g" % current_range)
        self.send("SYST:ZCOR ON")
        self.send("SYST:ZCH OFF")
        logging.info("Keithley.setup_current_measurements() done.")


    def read_measurement(self):
        """
        Proceed to an individual measurement (READ?) and parse
        the resulting output (trying to take into account the
        various Keithley idiosyncracies).
        """
        logging.info("Keithley.read_measurements() called.")
        s = self.send("READ?")
        elts = s.split(",")
        if len(elts) < 2: # has at minimum 2 fields, sometimes three...
            logging.error("READ?: no/incomplete data from the Keithley.")
            raise IOError("READ?: no/incomplete data from the Keithley.")

        measure = float(elts[0].replace('A', '')) # sometime the unit is there
        logging.info("   measure = %g" % measure)
        logging.info("Keithley.read_measurements() done.")
        return measure

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
