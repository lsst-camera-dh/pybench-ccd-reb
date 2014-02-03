#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

# ==================================================================
#
# SkyDice
#
# Low level control for the LakeShore 325
# Minimal model RS232 Temperature readings
#
# Authors: Laurent Le Guillou
#
# ==================================================================

import sys
import os, os.path
import time
import datetime
import serial


# ==================================================================

class LakeShoreError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# ==================================================================

class LakeShore:

# ------------------------------------------------------------------

    def __init__(self, 
                 port = '/dev/ttyS0',
                 debug = True):
        """
        Create a LakeShore instance.
        """
        
        # ---- Serial port configuration ------
        self.port = port
        self.baudrate = 9600
        self.echo = 0
        self.rtscts = 0
        self.xonxoff = 0
        self.timeout = 0.5 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_ODD
        self.bytesize = serial.SEVENBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None
        self.EOL = '\n'              # '\n' = 'LF'
        # end of line EOL = '\r' (confirmed & tested)

        # ---- debug mode
        self.debug = debug

# ------------------------------------------------------------------

    def open(self):
        """
        Open and initialize the serial port to communicate
        with the instrument.
        """

        if self.debug: print >>sys.stderr, "LakeShore325: Opening port %s ..." % self.port
        
        self.serial_port = serial.Serial(port = self.port, 
                                         baudrate = self.baudrate,
                                         rtscts = self.rtscts, 
                                         xonxoff = self.xonxoff,
                                         bytesize = self.bytesize, 
                                         parity = self.parity,
                                         stopbits = self.stopbits, 
                                         timeout = self.timeout)
        
        if ( (self.serial_port == None) or
             not(self.serial_port.isOpen()) ):
            raise IOError("LakeShore325: " + 
                          "Failed to open serial port %s" % self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("LakeShore325: " + 
                           "LakeShore is not echoing on serial port %s") % 
                          self.port)
        
        
        if self.debug: 
            print >>sys.stderr, ( "LakeShore325: Opening port %s done." % 
                                  self.port )


# ------------------------------------------------------------------            

    def close(self):
        """
        Close the serial port.
        """
        if ( self.serial_port and
             self.serial_port.isOpen() ):
            self.serial_port.close()

# ------------------------------------------------------------------ 
            
    def __del__(self):
        self.close()

# ------------------------------------------------------------------ 

    def reopen_if_needed(self):
        """
        Reopen the serial port if needed.
        """
        if not(self.serial_port):
            raise IOError("LakeShore325: " +
                          "LakeShore serial port should be opened first.")

        if not(self.serial_port.isOpen()): # open if port is closed
            self.open()


    def purge(self):
        """
        Purge the serial port to avoid framing errors.
        """
        self.serial_port.flushOutput()
        self.serial_port.flushInput()
        self.serial_port.readline() # To purge remaining bytes (???)

# ------------------------------------------------------------------ 
#
# Basic I/O with debugging information

    def write(self, command):
        """
        Send a command through the serial port.
        """
        if self.debug: print >>sys.stderr, \
                "LakeShore325: Sending command [" + command + "]"
        self.serial_port.write(command + self.EOL)


    def read(self, timeout = None):
        """
        Read the answer from the serial port.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """
        
        if self.debug: print >>sys.stderr, "LakeShore325: " + \
                "Reading serial port buffer"

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, "LakeShore325: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.readline() # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        
        # remove end of line
        answer = answer.strip()
        if self.debug: print >>sys.stderr, "LakeShore325: " + \
                "Received [" + answer + "]"

        return answer

# ------------------------------------------------------------------ 

    def echotest(self):
        """
        Verify communications with the LakeShore.
        Should return True if the communication has been established,
        and False otherwise.
        """
        
        self.reopen_if_needed()
        self.purge()
        
        # Send the command *IDN? to get the apparatus ID
   
        self.write("*IDN?")
        answer = self.read()
        if not(answer):
            return False

        return True

# # ------------------------------------------------------------------ 

#     def reset(self):
#         """
#         Reset the instrument to the factory default settings
#         (with the exception of all remote interface settings).
#         """
#         self.reopen_if_needed()
#         self.purge()

#         if self.debug: print >>sys.stderr, \
#                 "LakeShore325: Reset"
#         command = "*RST"
#         self.write(command)

# # ------------------------------------------------------------------ 
        
#     def clear(self):
#         """
#         Clear the instrument status.
#         """ 
#         self.reopen_if_needed()
#         self.purge()

#         if self.debug: print >>sys.stderr, \
#                 "LakeShore325: Clear Status registers"
#         command = "*CLS"
#         self.write(command)

# ------------------------------------------------------------------

    def get_temperature(self, channel = 'A'):
        """
        Take a temperature measurement (input A or B) and return the resulting value.
        """   

        if channel not in ['A', 'B']:
            raise ValueError("LakeShore325: Invalid channel [A|B]")

        self.reopen_if_needed()
        self.purge()

        self.write("KRDG? %s" % channel)
        answer = self.read()

        if not(answer):
            raise IOError("LakeShore325: Measurement: no data returned.")

        temperature = float(answer.strip())
        return temperature
            
    # --------------------------------------------------------------

    wavelength = property(get_temperature, 
                          doc="Current temperature (Kelvin)")

    # --------------------------------------------------------------

# ==================================================================
