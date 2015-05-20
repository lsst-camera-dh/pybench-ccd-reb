#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Lakeshore-325 (through Edo 'lakeshore' software and XML-RPC)
"""

# XML-RPC interface:
#
# connect() returns always 0
# close() returns always 0
# checkConnection() returns a NULL string or "325"
# getTempPower() returns [Ta Tb Power]
# status() returns instrument status 
# help() this info !

from driver import Driver

import time
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

        self._model = 'Unknown'

        self.channels = ['A', 'B']

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
        print answer

        if answer == "":
            return False

        # QTH -> '69931'
        # XeHg -> '69911'

        if answer != '325':
            return False

        self._model = 'Lakeshore 325'

        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.checkConnection()


    def register(self, bench):
        self.open()
        time.sleep(2)
        connected = self.is_connected()
        if not(connected):
            raise IOError("Lakeshore controller not connected.")

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
        Return 0 (???)
        """
        return self.xmlrpc.status()

    def getTempPower(self):
        """
        Returns [Temperature A (C), Temperature B (C), Heating Power (W)]
        """
        answer = self.xmlrpc.getTempPower() 
        if len(answer) < 3:
            raise IOError("Lakeshore controller not responding properly.")
        
        result = [ float(answer[0]), float(answer[1]), float(answer[2]) ]
        return result


    def getTemperature(self, channel):
        """
        Returns the temperature of channel 'channel' in Celsius.
        """
        if channel not in self.channels:
            raise ValueError("Unknown channel %s" % str(channel))

        result = self.getTempPower()
        temp = { 'A': result[0], 'B': result[1] }
        return temp[channel]

    def getPower(self):
        """
        Returns the heating power in Watts.
        """
        result = self.getTempPower()
        return result[2]


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
                'TEMPA',
                'TEMPB',
                'POWER']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver', 
            'TEMPA'  : '[Celsius] temperature A',
            'TEMPB'  : '[Celsius] temperature B',
            'POWER'  : '[W] heating power'
            }

        result = self.getTempPower()

        values = {
            'MODEL'  : self._model,
            'DRIVER' : 'lakeshore / thermal_lakeshore', 
            'TEMPA'  : float(result[0]),
            'TEMPB'  : float(result[1]),
            'POWER'  : float(result[2])
            }

        return keys, values, comments

# TODO: add programmed temperature as 'TEMP_SET'

    # ===================================================================
