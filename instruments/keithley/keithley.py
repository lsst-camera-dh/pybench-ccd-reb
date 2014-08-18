#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

# ==================================================================
#
# LSST (recycled from DICE)
#
# Low level control for the Multimeter - Keithley (6514, 2000)
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

class MultimeterError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# ==================================================================

class Multimeter:
# ------------------------------------------------------------------

    def __init__(self, 
                 port = '/dev/ttyS0',
                 debug = True):
        """
        Create a Multimeter instance.
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
        # end of line EOL = '\r' (confirmed & tested)

        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10


        # ---- default multimeter settings  
        # trigger frequency expressed in
        # power line (50Hz/60Hz) cycle number 
        self.cycles = 1  

        # ---- modes / ranges

        self.modes = { "current:ac" : "CURR:AC",
                       "current:dc" : "CURR:DC",
                       "voltage:ac" : "VOLT:AC",
                       "voltage:dc" : "VOLT:DC",
                       "resistance" : "RES",
                       "resistance:4" : "FRES" }

        self.modes_names = self.modes.keys()
                       

        self.ranges = { "current:ac" : 3.1,
                        "current:dc" : 3.1,
                        "voltage:ac" : 757.5,
                        "voltage:dc" : 1000.,
                        "resistance" : 120e6,
                        "resistance:4" : 120e6 }
       
# ------------------------------------------------------------------

    def open(self):
        """
        Open and initialize the serial port to communicate
        with the instrument.
        """

        if self.debug: print >>sys.stderr, "Keithley6514: Opening port %s ..." % self.port
        
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
            raise IOError("Keithley6514: " + 
                          "Failed to open serial port %s" % self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("Keithley6514: " + 
                           "Multimeter is not echoing on serial port %s") % 
                          self.port)
        
        
        if self.debug: 
            print >>sys.stderr, ( "Keithley6514: Opening port %s done." % 
                                  self.port )

        self.clear()

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
            raise IOError("Keithley: " +
                          "Multimeter serial port should be opened first.")

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
                "Keithley: Sending command [" + command + "]"
        self.serial_port.write(command + self.EOL)


    def read(self, timeout = None):
        """
        Read the answer from the serial port.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """
        
        if self.debug: print >>sys.stderr, "Keithley: " + \
                "Reading serial port buffer"

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, "Keithley: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.readline() # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        
        # remove end of line
        answer = answer.strip()
        if self.debug: print >>sys.stderr, "Keithley: " + \
                "Received [" + answer + "]"

        return answer

# ------------------------------------------------------------------ 

    def echotest(self):
        """
        Verify communications with the Multimeter.
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

# ------------------------------------------------------------------ 

    def reset(self):
        """
        Reset the instrument to the factory default settings
        (with the exception of all remote interface settings).
        """
        self.reopen_if_needed()
        self.purge()

        if self.debug: print >>sys.stderr, \
                "Keithley: Reset"
        command = "*RST"
        self.write(command)

# ------------------------------------------------------------------ 
        
    def clear(self):
        """
        Clear the instrument status.
        """ 
        self.reopen_if_needed()
        self.purge()

        if self.debug: print >>sys.stderr, \
                "Keithley: Clear Status registers"
        command = "*CLS"
        self.write(command)

# ------------------------------------------------------------------ 
    
    def check_error_status(self):
        """
        Get the various error status, clear them, and may
        raise the corresponding Exception (if needed).
        """

        self.reopen_if_needed()
        self.purge()

        # First, get (and clear) the Standard Event Status Register

        time.sleep(1)

        command = "*ESR?"
        self.write(command)
        answer = self.read()
        if not(answer):
            raise IOError("Keithley: *ESR? command failed (no answer).")
        try:
            esr = int(answer)
        except ValueError:
            raise IOError("Keithley: " +
                          "*ESR? command failed (invalid answer [1]).")


        self.clear()

        if (esr & 0x20):
            # Command Error. Set when a syntax type error is detected
            # in a command from the bus. The parser is reset and parsing
            # continues at the next byte in the input stream.
            raise MultimeterError("Keithley: PowerSupply Command Error. " +
                          "A syntax type error has been detected " +
                          "in a command from the bus. " +
                          "The parser has been reset and parsing " +
                          "continues at the next byte in the input stream.")

        if (esr & 0x10):
            # Execution Error. Set when an error is encountered while
            # attempting to execute a completely parsed command.
            # The appropriate error number will be reported in 
            # the Execution Error Register

            # Now reading (and clearing) the Execution Error Register

            command = "EER?"
            self.write(command)
            answer = self.read()
            if not(answer):
                raise IOError("Keithley: EER? command failed (no answer).")
            try:
                eer = int(answer)
            except ValueError:
                raise IOError("Keithley: " +
                              "EER? command failed (invalid answer [1]).")

            if (eer >= 1) and (eer <= 99):
                raise MultimeterError("Keithley: Hardware error.")

            if eer == 116:
                raise MultimeterError("Keithley: Invalid recall of data.")

            if eer == 117:
                raise MultimeterError("Keithley: Corrupted internal data.")

            if eer == 120:
                raise MultimeterError("Keithley: " +
                              "Numerical specified value was too big " + 
                              "or too small.")

            if eer == 123:
                raise MultimeterError("Keithley: " +
                              "Illegal recall requested.")

            if eer == 124:
                raise MultimeterError("Keithley: " +
                              "Illegal range change requested.")


        if (esr & 0x08):
            # Verify Timeout Error. Set when a parameter is set with 'verify'
            # specified and the value is not reached within 5 secs.
            raise MultimeterError("Keithley: Verify Timeout Error. " +
                          "Set when a parameter is set with 'verify' " +
                          "specified and the value is not reached " +
                          "within 5 secs.")

        if (esr & 0x04):
            # Query Error. Appropriate number is reported in 
            # the Query Error register
            raise MultimeterError("Keithley: Query Error.")

# ------------------------------------------------------------------ 



# ------------------------------------------------------------------ 

    def setup(self, mode = "voltage:dc", rang = None, cycles = 1):
        """
        Instrument Setup. Choose the measurement mode 'mode' between
        the following value:
                            'current:ac'
                            'current:dc'
                            'voltage:ac'
                            'voltage:dc'
                            'resistance'
                            'resistance:4'

        'rang' is the multimeter range.

        'cycles' is number of power line frequency cycles between
        measurements : e.g. 1 => dt = 1/50Hz or 1/60Hz.
        """

        if not(mode in self.modes_names):
            raise ValueError("Keithley: unknown measurement mode.")

        if (cycles < 0.01) or (cycles > 10):
            raise ValueError("Keithley: <cycles> out of [0.01-10] range.")


        self.reopen_if_needed()
        self.purge()

        # First, switch to the selected measurement mode
        command = ":FUNC '%s'" % self.modes[mode]
        self.write(command)
        self.check_error_status()
        
        # Select the trigger frequency 
        command = ":SENS:%s:NPLC %f" % (self.modes[mode], cycles)
        self.write(command)
        self.check_error_status()
        self.cycles = cycles # after it is done

        # Select the range
        if rang == None:
            range_str = "DEF"
        else:
            range_str = str(rang)
            
        # command = "SENS:%s:RANG %s" % (self.modes[mode], range_str)
        command = ":SENS:%s:RANG %s" % (self.modes[mode], range_str)
        self.write(command)
        self.check_error_status()
        
# ------------------------------------------------------------------

    def measure(self, count, display = False):
        """
        Take a measurement and get the resulting data.
        """   
        self.reopen_if_needed()
        self.purge()

        #TODO check the command TRIG:COUN and TRAC:FEED:CONT
        #to understand the timing of I/O with serial port.

        self.write(":ABOR")

        self.write(':INIT:CONT OFF')
        self.write(':TRIG:COUN ' + str(count))
        if not(display):
            self.write(':DISP:ENAB ON')
            
        self.write(":TRAC:FEED:CONT NEXT")
        self.write(':INIT')

        # Time to wait

        wait = 10. * ((self.cycles / 50.0) * count)
        if self.debug: print >>sys.stderr, "Waiting", wait, "sec" 
        time.sleep(wait)
 
        if not(display): # retablish display
            self.write(':DISP:ENAB ON')

        self.write(':TRAC:DATA?')

        if self.debug: print >>sys.stderr, "Reading buffer"
        answer = self.read(5)

        if not(answer):
            raise IOError("Keithley: Measurement: no data returned.")

        self.check_error_status()

        return answer
            
# ------------------------------------------------------------------

    def scroll_text(self, msg):

        self.reopen_if_needed()
        self.purge()

        length = 12 # max number of char displayed
        l = len(msg)
        msgmsg = msg + l * " "
        self.write(":ABOR")
        self.write(":DISP:TEXT:STAT 1")
        for i in xrange(l):
            start = i % l
            stop = start + 12
            self.write(":DISP:TEXT:DATA '%s'" % msgmsg[start:stop])
            time.sleep(.5)

        self.write(":DISP:TEXT:STAT 0")

# ==================================================================
