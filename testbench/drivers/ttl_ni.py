#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the National Instrument board 
which generates ttl signals (through Edo software and XML-RPC)
"""

# XML-RPC interface:
#
# connect()         returns always 0
# close()           returns always 0
# checkConnection() returns TRUE or FALSE
# openShutter()     opens the security shutter
#                         returns the state (1: opened, 0: closed)
# closeShutter()    closes the security shutter
#                         returns the state (1: opened, 0: closed)
# openMellesShutter()     opens the Melles shutter
#                         returns the state (1: opened, 0: closed)
# closeMellesShutter()    closes the Melles shutter
#                         returns the state (1: opened, 0: closed)
# moveFilterWheel() moves the filter wheel
#                         check movement with the status() method
# homeFilterWheel() moves the filter wheel to the home position: filter 300nm
#                         check movement with the status() method
# selectQTH()       selects QTH lamp
#                         check state with status() method
# selectXeHg()      selects XeHg lamp
#                         check state with status() method
# status()          returns [ secShutterState(0,1), mellesShutterState(0,1),
#                         wheel(-1: moving, 0: home, 1: other), ("QTH","XeHg")

import time
import xmlrpclib

from driver import Driver

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
        
        self.filter_position = None # unknown by default

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
        return self.xmlrpc.checkConnection()


    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError(
                "TTL board not connected (or ttl software not running).")

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
        Return [ secShutterState(0,1), mellesShutterState(0,1),
                 wheel(-1: moving, 0: home, 1: other), ("QTH","XeHg") ]
        """
        return self.xmlrpc.status()

    # ===================================================================

    def openSafetyShutter(self, wait=False):
        """
        Open the safety shutter.
        Return the shutter state (1: opened, 0: closed).
        """
        answer = self.xmlrpc.openShutter()
        if wait:
            while not(self.SafetyShutterIsOpen()):
                time.sleep(0.5)
        return answer

    def closeSafetyShutter(self, wait=False):
        """
        Close the safety shutter.
        Return the shutter state (1: opened, 0: closed).
        """
        answer = self.xmlrpc.closeShutter()
        if wait:
            while self.SafetyShutterIsOpen():
                time.sleep(0.5)
        return answer

    def SafetyShutterIsOpen(self):
        """
        Return the safety shutter state (Open = True, Close = False)
        """
        status = self.status()
        return bool(status[0])

    # ===================================================================

    def openMellesShutter(self, wait=False):
        """
        Open the Melles shutter.
        Return the shutter state (1: opened, 0: closed).
        """
        answer = self.xmlrpc.openMellesShutter()

        if wait:
            while not(self.MellesShutterIsOpen()):
                time.sleep(0.5)

        return answer

    def openShutter(self, wait=False):
        return self.openMellesShutter(wait = wait)

    def closeMellesShutter(self, wait = False):
        """
        Close the Melles shutter.
        Return the shutter state (1: opened, 0: closed).
        """
        answer = self.xmlrpc.closeMellesShutter()

        if wait:
            while self.MellesShutterIsOpen():
                time.sleep(0.5)

        return answer 

    def closeShutter(self, wait=False):
        return self.closeMellesShutter(wait = wait)

    def MellesShutterIsOpen(self):
        """
        Return the Melles shutter state (Open = True, Close = False)
        """
        status = self.status()
        return bool(status[1])

    def shutterIsOpen(self):
        return self.MellesShutterIsOpen()

    # ===================================================================

    def homeFilterWheel(self):
        """
        Move the filter wheel to its home position.
        You should check the wheel movement with the status() method.
        """
        self.filter_position = 1
        return self.xmlrpc.homeFilterWheel()

    def moveFilterWheel(self):
        """
        Move the filter wheel (by one step).
        You should check the wheel movement with the status() method.
        """
        if self.filter_position is not None:
            self.filter_position += 1
        return self.xmlrpc.moveFilterWheel()

    def filterWheelIsMoving(self):
        """
        Tell if the filter wheel is still moving (True) or not (False).
        """
        status = self.status()
        if status[2] == -1:
            return True
        return False

    # Higher level function
    def moveFilter(self, position = 1):
        """
        Move the filter wheel to the specified position [1-6].
        You should check the wheel movement with the status() method.
        Wait until target position is reached.
        """

        if position not in range(1,7):
            raise ValueError("Invalid filter position: should be in [1-6]")

        self.homeFilterWheel()
        while self.filterWheelIsMoving():
            time.sleep(1)

        for i in xrange(position - 1):
            self.moveFilterWheel()
            while self.filterWheelIsMoving():
                time.sleep(1)

    # ===================================================================

    def getLamp(self):
        """
        Return the name of the select lamp.
        """
        status = self.status()
        if len(status) < 4:
            return None
        return status[3]

    def selectQTH(self, wait=False):
        """
        Move the flipping mirror to get the flux from the QTH lamp.
        You may check the mirror state with the status() method.
        """
        answer = self.xmlrpc.selectQTH()
        if wait:
            while not(self.getLamp() == 'QTH'):
                time.sleep(0.5)

        return answer

    def selectXeHg(self, wait=False):
        """
        Move the flipping mirror to get the flux from the XeHg lamp.
        You may check the mirror state with the status() method.
        """
        answer = self.xmlrpc.selectXeHg()
        if wait:
            while not(self.getLamp() == 'XeHg'):
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
                'DRIVER']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver' 
            }

        values = {
            'MODEL'  : 'National Instrument board',
            'DRIVER' : 'ttl / ttl_ni' 
            }

        # status

        status = self.status()

        # LMIRROR  -> QTH or XeHg
        key = 'LMIRROR'
        comment = 'lamps mirror position : QTH or XeHg'
        value = status[3]
        keys.append(key)
        values[key] = value
        comments[key] = comment

        # SAFSHUT  -> 0 / 1
        key = 'SAFSHUT'
        comment = 'safety shutter position 0=closed 1=open'
        value = status[0]
        keys.append(key)
        values[key] = value
        comments[key] = comment

        # SPHSHUT  -> 0 / 1
        key = 'SPHSHUT'
        comment = 'integrating sphere shutter position 0=closed 1=open'
        value = status[1]
        keys.append(key)
        values[key] = value
        comments[key] = comment

        # LMPFILT  -> unknown (-1) or position [1-???]
        key = 'LMPFILT'
        comment = 'lamp filter position'
        if self.filter_position == None:
            value = -1
        else:
            value = self.filter_position
        keys.append(key)
        values[key] = value
        comments[key] = comment

        data = []

        return keys, values, comments, data

    # ===================================================================
