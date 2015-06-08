#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Ultra-thin abstraction layer for the various devices
on the LPNHE LSST CCD testbench.
"""

class Driver(object):

    # Minimal functions requested
    # Methods should be overwritten

    def __init__(self, identifier, **kargs):
        self.identifier = identifier
        self.__dict__.update(**kargs)

    def open(self):
        """
        Open the hardware connection.
        """
        pass

    def checkConnection(self):
        """
        Check if the connection is established with the hardware.
        """
        return ""

    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        """
        return True

    def close(self):
        """
        Close the connection the hardware.
        """
        pass

    def register(self, bench):
        """
        Connect and check the connection to the device.
        """
        self.bench = bench
        return True

    def get_meta(self):
        """
        Return meta data describing the current state of the instrument. 
        Useful to fill the FITS headers.
        """
        return [], {}, {}, []

