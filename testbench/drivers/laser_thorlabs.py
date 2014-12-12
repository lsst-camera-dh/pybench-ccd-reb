#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Thorlabs Laser (through Edo software and XML-RPC)
"""

# XML-RPC interface:
#
# connect() returns always 0
# close() returns always 0
# checkConnection() returns a NULL string or the model name
# select(int index) enables channel if index>0, otherwise disables
#                   where abs(index) = [1-4]
# getCurrent(int index) returns a string with the target current
#                       -1 if index out of range
# setCurrent(int index,double value) returns 0 or -1 if index out of range
# getPower(int index) returns actual output power
#                             -1 if index out of range
# enable() enables lasing, returns 0
# disable() disables lasing, returns 0


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

        # Available channels
        self.allchannels = [1,2,3,4]


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

        if 'THORLABS' not in answer:
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.checkConnection()


    def register(self):
        Driver.register(self)

        self.open()
        connected = self.is_connected()
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

        if abs(channel) not in self.allchannels:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in %s" % 
                str(self.allchannels))
        self.xmlrpc.select(channel)


    def unselect(self, channel):
        """
        Disable laser channel 'channel'. 'channel' should be in [1-4].
        """
        if channel not in self.allchannels:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in %s" %
                str(self.allchannels))
        self.xmlrpc.select(-channel)


    def getCurrent(self, channel):
        """
        Returns the current (in mA) set for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in self.allchannels:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in %s" %
                str(self.allchannels))
        
        return float(self.xmlrpc.getCurrent(channel))


    def setCurrent(self, channel, current):
        """
        Sets the current (in mA) for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in self.allchannels:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in %s" % 
                str(self.allchannels))
        
        return self.xmlrpc.setCurrent(channel, current)


    def getPower(self, channel):
        """
        Returns the actual output power (in mW) for channel 'channel'.  
        Channel should be in [1-4].
        """
        if channel not in self.allchannels:
            raise ValueError(
                "Invalid Laser Thorlabs channel id. Should be in %s" %
                str(self.allchannels))
        
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

        for channel in self.allchannels:
            # current 
            key = 'CH_CURR%d' % channel
            comment = '[mA] Current in laser diode %d in mA' % channel
            value = self.getCurrent(channel)
            keys.append(key)
            values[key] = value
            comments[key] = comment

            # current 
            key = 'CH_POW%d' % channel
            comment = '[mW] Output Power for laser diode %d in mW' % channel
            value = self.getPower(channel)
            keys.append(key)
            values[key] = value
            comments[key] = comment

        return keys, values, comments

    # ===================================================================
