#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Oriel lamps (through Edo 'oriel' software and XML-RPC)
"""

# XML-RPC interface:
#
# connect() returns [int, string] 1:ok  0:failed 2:port already opened
# close() returns 1 on error 0 otherwise
# checkConnection() returns a NULL string or the model name
# status() returns instrument status [connected, on/off, ramping, controlling]

# getPresetCurrent() returns double
# setPresetCurrent(double)
# getPresetPower() returns double
# setPresetPower(double)
# setFluxControl(int) 1:on 0:off (QTH lamp must be on)
# getAmps() returns a double
# getVolts() returns a double
# getWatts() returns a double
# getHours() returns a double
# power(int)  1:power on 0:power off WARNING: wait 20 seconds to complete
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

        # QTH -> '69931'
        # XeHg -> '69911'

        if answer not in ['69931','69911']:
            return False

        if answer == '69931':
            self._model = 'QTH 69931'
        elif answer == '69911':
            self._model = 'XeHg 69911'

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
            raise IOError("Oriel lamp not connected.")

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
        Return [ connected, on/off, ramping, controlling ]
        """
        return self.xmlrpc.status()

    def getPresetPower(self):
        """
        Returns the preset power for the lamp in mW (???).
        """
        return self.xmlrpc.getPresetPower() 


    def setPresetPower(self, power):
        """
        Set the power for the lamp in mW (???).
        """
        return self.xmlrpc.setPresetPower(float(power))


    def getPresetCurrent(self):
        """
        Returns the preset current for the lamp in mA (???).
        """
        return self.xmlrpc.getPresetCurrent() 


    def setPresetCurrent(self, power):
        """
        Set the current for the lamp in mA (???).
        """
        return self.xmlrpc.setPresetCurrent(float(power))


    def isRamping(self):
        """
        Return True if the lamp is ramping up or down.
        """
        status = self.status()
        if len(status) < 4:
            return False

        if status[2] == 1:
            return True

        return False

    def setFluxControl(self, flag):
        """
        Activate/deactivate the flux control (QTH only).
        """
        query = 0
        if flag: query = 1

        return self.xmlrpc.setFluxControl(query)

    def isFluxControlled(self):
        """
        Return True if the flux is controlled, False otherwise.
        """
        status = self.status()
        if len(status) < 4:
            return False

        if status[3] == 1:
            return True

        return False

    def power(self, flag, wait=False):
        """
        Turn on/off the lamp. 
        WARNING: wait 20 seconds to complete.
        """
        query = 0
        if flag: query = 1

        answer = self.xmlrpc.power(query)
        if wait:
            while self.isRamping():
                time.sleep(0.5)

        return answer

    def on(self, wait=False):
        return self.power(True, wait)

    def off(self, wait=False):
        return self.power(False, wait)

    def isOn(self):
        status = self.status()
        if len(status) < 4:
            return False

        if status[1] == 1:
            return True

        return False

    def getAmps(self):
        return self.xmlrpc.getAmps()

    def getVolts(self):
        return self.xmlrpc.getVolts()

    def getWatts(self):
        return self.xmlrpc.getWatts()

    def getHours(self):
        return self.xmlrpc.getHours()

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
                'ON',
                'CONTROL',
                'CURRENT',
                'VOLTAGE',
                'POWER',
                'TIME']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver', 
            'ON'     : '1 = power on, 0 = power off',
            'CONTROL': '1 = regulated flux, 0 otherwise',
            'CURRENT': '[A] lamp current',
            'VOLTAGE': '[V] lamp voltage',
            'POWER'  : '[W] lamp power',
            'TIME'   : '[hours] lamp life duration'
            }

        values = {
            'MODEL'  : 'ORIEL ' + self._model,
            'DRIVER' : 'oriel / lamp_oriel', 
            'ON'     : int(self.isOn()),
            'CONTROL': int(self.isFluxControlled()),
            'CURRENT': self.getAmps(),
            'VOLTAGE': self.getVolts(),
            'POWER'  : self.getWatts(),
            'TIME'   : self.getHours()
            }

        data = []

        return keys, values, comments, data

    # ===================================================================
