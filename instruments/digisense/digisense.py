#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

# ==================================================================
#
# SkyDice
#
# Low level control for the temperature Controller Digi-Sense
#
# Authors: Pier-Francesco Rocci & Laurent Le Guillou
#
# ==================================================================

import sys
import os, os.path
import time
import datetime
import serial


# ==================================================================

class TemperatureError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# ==================================================================

class Temperature:

# ------------------------------------------------------------------

    def __init__(self, 
                 port = '/dev/ttyUSB5',
                 debug = True):
        """
        Create a DigiSense instance.
        """
        
        # ---- Serial port configuration ------
        self.port = port
        self.baudrate = 9600
        self.echo = 0
        self.rtscts = 0
        self.xonxoff = 0
        self.timeout = 0.5 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None
        self.EOL = '\r'              # '\r' = 'CR'

        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10
       
# ------------------------------------------------------------------

    def open(self):
        """
        Open and initialize the serial port to communicate
        with the instrument.
        """

        if self.debug: print "Digi-Sense: Opening port %s ..." % self.port
        
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
            raise IOError("DigiSense: " + 
                          "Failed to open serial port %s" % self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("DigiSense: " + 
                           "Controller is not echoing on serial port %s") % 
                          self.port)
        
        
        if self.debug: 
            print >>sys.stderr, ( "DigiSense: Opening port %s done." % 
                                  self.port )

        self.setup()

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
            raise IOError("DigiSense: " +
                          "Controller serial port should be opened first.")

        if not(self.serial_port.isOpen()): # open if port is closed
            self.open()


    def purge(self):
        """
        Purge the serial port to avoid framing errors.
        """
        self.serial_port.flushOutput()
        self.serial_port.flushInput()
        self.serial_port.readline()

# ------------------------------------------------------------------ 
#
# Basic I/O with debugging information
#

    def write(self, command):
        """
        Send a command through the serial port.
        """
        if self.debug: print >>sys.stderr, \
                "DigiSense: Sending command [" + command + "]"
        self.serial_port.write(command + self.EOL)


    def read(self, timeout = None):
        """
        Read the answer from the serial port.
        Return it as a string.
        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """
        
        if self.debug: print >>sys.stderr, "DigiSense: " + \
                "Reading serial port buffer"

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, "DigiSense: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.readline() # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        answer = answer.strip()
        if self.debug: print >>sys.stderr, "DigiSense: " + \
                "Received [" + answer + "]"

        return answer

    # ---------- Send a command and get the answer -----------

    def send(self, cmd):
        """
        Send a command (DigiSense serial language) 
        and return the answer (if any).

        @param cmd: the command to send.
        """

        if len(cmd) < 1:
            raise ValueError("Invalid command")

        command = chr(2) + cmd

        # Now send it
        self.write(command)

        # Parsing the answer (to detect errors)

        answer = self.read()
        print "ANSWER = ", answer

        if len(answer) < 1:
            raise TemperatureError(("DigiSense: " +
                                    "Controller does not answer " +
                                    "on serial port on command [%s]") % command)

        if answer[0] == chr(2):
            # Answer returned OK
            answer = answer[1:]
        elif answer[0] == chr(6): # ACK
            # success
            answer = answer[1:]
        elif answer[0] == chr(15): # NAK -> problem
            raise TemperatureError(("DigiSense: " +
                                    "invalid command [%s]") % command)
        else:
            raise TemperatureError(("DigiSense: " +
                                    "strange answer... [%s]") % command)

        return answer

# ------------------------------------------------------------------ 

    def echotest(self):
        """
        Verify communications with the DigiSense temperature controller.
        Should return True if the communication has been established,
        and False otherwise.
        """
        
        self.reopen_if_needed()
        self.purge()
        
        # Send the command T1V to get the apparatus firmware version
   
        answer = self.send("T1V")
        if not(answer):
            return False

        return True

# ------------------------------------------------------------------ 

    def setup(self):
        """
        Instrument Setup.            
        """

        self.reopen_if_needed()
        self.purge()

        # Third Temperature Unit   
        cmd = "T1U2" # Kelvin
        self.send(cmd)

# ------------------------------------------------------------------

    def measure(self):
        """
        Take a measurement and get the resulting data.
        """   
        self.reopen_if_needed()
        self.purge()
        
        #Take the measure
        command = "T1PV"
        answer = self.send(command)

        if not(answer):
            raise IOError("DigiSense: no data returned.")
        
        ### '\x02PV  298.0\r\n'
        parts = (answer.strip()).split()
        if len(parts) < 2:
            raise TemperatureError("DigiSense: incomplete data returned.")

        try:
            temperature = float(parts[1])
        except ValueError:
            raise TemperatureError("DigiSense: invalid data returned.")
            
        return temperature
            

# ==================================================================
