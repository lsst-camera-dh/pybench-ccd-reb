#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Triax Monochromator (through Edo software and XML-RPC)
"""

# XML-RPC interface: ('triax')
#
# connect() returns always 0
# close() returns always 0
# checkConnection() returns a '1' if connected and a '0' otherwise
# status() returns instrument status --> 1 = ready, 0 = not ready
# getWavelength() returns wavelength (double)
# setWavelength(double) 
# moveRelative(int) 
# getInSlit() returns int
# setInSlit(int) 
# getOutSlit() returns int
# setOutSlit(int) 
# getGrating() returns current grating, int
# setGrating(int)
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

        # Available gratings
        # TODO: add resolution, blaze angle, etc...
        self.gratings_properties = { 0: {'name': 'G0',
                                         'range': [200.0, 600.0]}, 
                                     1: {'name': 'G1',
                                         'range': [600.0, 1100.0]}, 
                                     2: {'name': 'G2',
                                         'range': [1100.0, 2600.0]}
                                     }


        self.gratings = self.gratings_properties.keys()


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

        if answer != '1':
            return False

        return True


    def checkConnection(self):
        """
        Returns '1' if connected.
        """
        return self.xmlrpc.checkConnection()


    def register(self, bench):
        self.open()
        time.sleep(2)
        connected = self.is_connected()
        if not(connected):
            raise IOError("Monochromator Triax not connected.")

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
        Return Monochromator status. 
        0 = not ready (moving, etc), 1 = ready.
        """
        return self.xmlrpc.status()

    def isReady(self):
        """
        Tell if the Monochromator is ready.
        """
        return(self.status() == 1)

    # ===================================================================
    # Wavelength

    def getWavelength(self):
        """
        Return the current wavelength.
        """
        return self.xmlrpc.getWavelength()

    def setWavelength(self, wavelength, wait = False):
        """
        Set the wavelength to <wavelength>.
        (takes time)
        """
        answer = self.xmlrpc.setWavelength(float(wavelength))
        if wait:
            while not(B.triax.isReady()):
                time.sleep(0.5)
        return answer

    # def moveRelative(int) 

    # ===================================================================
    # Slits

    def getInSlit(self):
        """
        Return the width of the entrance slit (unit ???).
        """
        return self.xmlrpc.getInSlit()

    def setInSlit(self, width, wait = False):
        """
        Set the width of the entrance slit (unit ???).
        """
        # TODO : check allowed values
        answer = self.xmlrpc.setInSlit(int(width))
        if wait:
            while not(B.triax.isReady()):
                time.sleep(0.5)
        return answer

    def getOutSlit(self):
        """
        Return the width of the exit slit (unit ???).
        """
        return self.xmlrpc.getOutSlit()

    def setOutSlit(self, width, wait):
        """
        Set the width of the exit slit (unit ???).
        """
        # TODO : check allowed values
        answer = self.xmlrpc.setOutSlit(int(width))
        if wait:
            while not(B.triax.isReady()):
                time.sleep(0.5)
        return answer

    # ===================================================================
    # Gratings

    def getGrating(self):
        """
        Return the current selected grating.
        """
        return self.xmlrpc.getGrating()

    def setGrating(self, grating, wait=False):
        """
        Set the grating to <grating>.
        """
        if grating not in self.gratings:
            raise ValueError("Invalid grating. Shoud be in %s" 
                             % self.gratings )

        answer = self.xmlrpc.setGrating(int(grating))
        if wait:
            while not(B.triax.isReady()):
                time.sleep(0.5)
        return answer

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
                'WVLGTH',
                'INSLIT',
                'OUTSLIT',
                'GRATING']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver',
            'WVLGTH' : '[nm] selected wavelength',
            'INSLIT' : '[unit???] Width of the entrance slit',
            'OUTSLIT': '[unit???] Width of the exit slit',
            'GRATING': 'Selected grating'
            }

        values = {
            'MODEL'  : 'Triax',
            'DRIVER' : 'triax / monochromator_triax',
            'WVLGTH' : self.getWavelength(),
            'INSLIT' : self.getInSlit(),
            'OUTSLIT': self.getOutSlit(),
            'GRATING': self.getGrating()
            }

        return keys, values, comments

    # ===================================================================
