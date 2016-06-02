#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Phytron motor holding the 55Fe X-ray source.
(through Edo 'phytron' software and XML-RPC)
"""

# XML-RPC interface:
#
# connect() returns [int] 1:ok  0:failed
# close() returns 1 on error 0 otherwise
# checkConnection() returns a NULL string or the model name
# status() returns instrument status [connected, on/off, ramping, controlling]

# getPosition() returns double 
# park() 
# goCCD()
# stop()
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

        if answer not in ['1']:
            return False

        # self._model = ???
        self._model = "Phytron motor (?)"

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
            raise IOError("Phytron motor controller not connected.")

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
        Return [ Connected,
                 True = at target / False = moving, 
                 True = parked / False = on CCD ]
        """
        return self.xmlrpc.status()


    def isMoving(self):
        """
        Returns True if moving, False otherwise.
        """
        return not(self.xmlrpc.status()[1])


    def isParked(self):
        """
        Returns True if moving, False otherwise.
        """
        return self.xmlrpc.status()[2]

    
    def getPosition(self):
        """
        Returns the motor position.
        """
        return self.xmlrpc.getPosition()


    def park(self, wait=True):
        """
        Park the 55Fe X-ray source.
        """
        answer = self.xmlrpc.park()
        if wait:
            while self.isMoving():
                time.sleep(0.5)
        return answer


    def goCCD(self, wait=True):
        """
        Put the 55Fe X-ray source in front of the CCD.
        """
        answer = self.xmlrpc.goCCD()
        if wait:
            while self.isMoving():
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
                'MOVING',
                'PARKED',
                'POS']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver', 
            'MOVING' : '1 = moving, 0 = on target',
            'PARKED' : '1 = parked, 0 otherwise',
            'POS'    : 'Xray arm position'
            }

        values = {
            'MODEL'  : 'Phytron motor ' + self._model,
            'DRIVER' : 'phytron / xray_phytron', 
            'MOVING' : int(self.isMoving()),
            'PARKED' : int(self.isParked()),
            'POS'    : float(self.getPosition())
            }

        data = []

        return keys, values, comments, data

    # ===================================================================
