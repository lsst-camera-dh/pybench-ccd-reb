#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Ultra-thin abstraction layer for the various devices
on the LPNHE LSST CCD testbench.
"""

class Driver(object):

    def __init__(self, identifier):
        self.identifier = identifier

    def open(self):
        """
        Open the hardware connection.
        """
        pass

    def checkConnection(self):
        """
        Check if the connection is established with the hardware.
        """
        return True



    
