#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the XYZ Pollux motors
"""

# XML-RPC interface:
#

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
        # self.devices = devices
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

        if 'THORLABS' not in answer:
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.checkConnection()


    def register(self):
        self.open()
        connected = self.checkConnection()
        if not(connected):
            raise IOError("Laser Thorlabs not connected.")

    def close(self):
        """
        Close the hardware connection.
        """
        self.xmlrpc.close()
        # TODO: Check errors


    # ===================================================================
    #  Instrument specific methods
    # ===================================================================

    def select(self, channel):
        """
        Enable laser channel 'channel'. 'channel' should be in [1-4].
        If channel is negative, Turn the channel off.
        """
        if abs(channel) not in [1,2,3,4]:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in [1-4]")
        self.xmlrpc.select(channel)


    def unselect(self, channel):
        """
        Disable laser channel 'channel'. 'channel' should be in [1-4].
        """
        if channel not in [1,2,3,4]:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in [1-4]")
        self.xmlrpc.select(-channel)


    def getCurrent(self, channel):
        """
        Returns the current (in mA) set for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in [1,2,3,4]:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in [1-4]")
        
        return float(self.xmlrpc.getCurrent(channel))


    def setCurrent(self, channel, current):
        """
        Sets the current (in mA) for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in [1,2,3,4]:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in [1-4]")
        
        return self.xmlrpc.setCurrent(channel, current)


    def getPower(self, channel):
        """
        Returns the actual output power (in mW) for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in [1,2,3,4]:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in [1-4]")
        
        return float(self.xmlrpc.getPower(channel))


    def enable(self):
        """
        Enable lasing.
        """
        return self.xmlrpc.enable()


    def disable(self):
        """
        Disable lasing.
        """
        return self.xmlrpc.disable()


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
            'MODEL'  : 'ThorLabs',
            'DRIVER' : 'laserthorlabs / pyBench' 
            }

        

        return keys, values, comments

    # ===================================================================
