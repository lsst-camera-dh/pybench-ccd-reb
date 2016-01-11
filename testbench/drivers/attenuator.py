#
# LSST / LPNHE
# Author: Laurent Le Guillou, Claire Juramy
#
"""
Testbench driver for the programmable attenuator (REB test bench)
"""

from driver import Driver

import xmlrpclib
import time

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
        self.att = 0

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
        return self.checkConnection()

    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        self.get_attenuation()
        return 'Weinschel'

    def register(self, bench):
        # self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("Attenuator device is not connected.")

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

    def get_attenuation(self):
        """
        Reads current attenuation from instrument.
        """
        self.att = self.xmlrpc.getAttenuation()
        return self.att

    def set_attenuation(self, a):
        """
        Set attenuation on instrument, read back and save value.
        """
        if a < 0 or a > 127:
            raise ValueError('Attenuator cannot be programmed to %d dB' % a)

        out = self.xmlrpc.setAttenuation(int(a))
        if not out:
            raise IOError('Failed to write to attenuator')
        time.sleep(0.5)
        self.get_attenuation()

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
                'VALUE']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver',
            'VALUE'  : '[dB] Current attenuation value'
            }

        values = {
            'MODEL'  : 'Attenuator',
            'DRIVER' : 'attenuator.py',
            'VALUE'  : self.att
            }

        data = []

        return keys, values, comments, data

    # ===================================================================
