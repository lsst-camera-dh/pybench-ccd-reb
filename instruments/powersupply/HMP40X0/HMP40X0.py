#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

# ==================================================================
#
# LSST
#
# Low level control for the Power Supply - HMP4030/HMP4040
#
# Authors: Laurent Le Guillou 
# Date: 2015-0-21
#
# ==================================================================

import sys
import os, os.path
import time
import datetime
import serial

# ==================================================================

class PowerSupplyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# ==================================================================

class PowerSupply(object):

# ------------------------------------------------------------------

    def __init__(self, 
                 device = '/dev/hmp4040',
                 debug = True):
        """
        Create a HMP40X0 PowerSupply instance.
        """
        
        # ---- Serial device configuration ------
        self.device = device
        # self.baudrate = 9600
        self.baudrate = 19200
        self.echo = 0
        self.rtscts = 0
        self.xonxoff = 0
        # self.timeout = 0.5 # Non-blocking & non waiting mode
        # self.timeout = 1.0 # Non-blocking & non waiting mode
        self.timeout = 0.5 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_device = None
        # self.EOL = '\r'              # '\r' = 'CR'
        self.EOL = '\n'              # '\n' = 'LF'
        # end of line EOL = '\r' (confirmed & tested)

        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10

        self.model = 'HMP40X0 unknown'
        self.allchannels = [1,2,3] 

# ------------------------------------------------------------------

    def open(self):
        """
        Open and initialize the serial device to communicate
        with the instrument.
        """

        if self.debug: print >>sys.stderr, "HMP40X0: Opening device %s ..." % self.device
        
        self.serial_device = serial.Serial(port = self.device, 
                                           baudrate = self.baudrate,
                                           rtscts = self.rtscts, 
                                           xonxoff = self.xonxoff,
                                           bytesize = self.bytesize, 
                                           parity = self.parity,
                                           stopbits = self.stopbits, 
                                           timeout = self.timeout)
        
        if ( (self.serial_device == None) or
             not(self.serial_device.isOpen()) ):
            raise IOError("HMP40X0: " + 
                          "Failed to open serial device %s" % self.device)
        
        self.serial_device.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("HMP40X0: " + 
                           "Power Supply is not echoing on serial device %s") % 
                          self.device)
        

        self.identification = self.get_serial() # *IDN? chain
        if 'HMP4040' in self.identification:
            self.model = 'HMP4040'
            self.allchannels = [1,2,3,4]
        elif 'HMP4030' in self.identification:
            self.model = 'HMP4030'
            self.allchannels = [1,2,3]
        else:
            print >>sys.stderr, "warning: unknown HMP40X0 model."
            self.model = 'HMP40X0 unknown'
            self.allchannels = [1,2,3] # no warranty

        
        if self.debug: 
            print >>sys.stderr, ( "HMP40X0: Opening device %s done." % 
                                  self.device )

        self.clear()

# ------------------------------------------------------------------            

    def close(self):
        """
        Close the serial device.
        """

        if ( self.serial_device and
             self.serial_device.isOpen() ):
            self.serial_device.close()

# ------------------------------------------------------------------ 
            
    def __del__(self):
        self.close()

# ------------------------------------------------------------------ 

    def reopen_if_needed(self):
        """
        Reopen the serial device if needed.
        """
        if not(self.serial_device):
            raise IOError("HMP40X0: " +
                          "Power Supply serial device should be opened first.")

        if not(self.serial_device.isOpen()): # open if device is closed
            self.open()


    def purge(self):
        """
        Purge the serial device to avoid framing errors.
        """
        self.serial_device.flushOutput()
        self.serial_device.flushInput()
        self.serial_device.readline() # To purge remaining bytes (???)

# ------------------------------------------------------------------ 
#
# Basic I/O with debugging information

    def write(self, command):
        """
        Send a command through the serial device.
        """
        if self.debug: print >>sys.stderr, \
                "HMP40X0: Sending command [" + command + "]"
        self.serial_device.write(command + self.EOL)


    def read(self, timeout = None):
        """
        Read the answer from the serial device.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """
        
        if self.debug: print >>sys.stderr, "HMP40X0: " + \
                "Reading serial device buffer"

        if timeout != None:
            self.serial_device.timeout = timeout
            if self.debug: print >>sys.stderr, "HMP40X0: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_device.readline() # return buffer
        
        # Restoring timeout to default one
        self.serial_device.timeout = self.timeout
        
        # remove end of line
        answer = answer.strip()
        if self.debug: print >>sys.stderr, "HMP40X0: " + \
                "Received [" + answer + "]"

        return answer

# ------------------------------------------------------------------ 

    def send(self, command, timeout = None):
        """
        Send a command through the serial device.
        Read the answer from the serial device.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """

        self.write(command)
        return self.read(timeout = timeout)

# ------------------------------------------------------------------ 

    def echotest(self):
        """
        Verify communications with the Power Supply.
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
                "HMP40X0: Reset"
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
                "HMP40X0: Clear Status registers"
        command = "*CLS"
        self.write(command)

# ------------------------------------------------------------------ 

    def get_error_status(self):
        """
        Get the various error status, clear them, and return them.
        does not raise exception (see check_error_status below).
        """

        self.reopen_if_needed()
        self.purge()

        # First, get (and clear) the Standard Event Status Register

        command = "*ESR?"
        self.write(command)
        answer = self.read()
        if not(answer):
            raise IOError("HMP40X0: *ESR? command failed (no answer).")
        try:
            esr = int(answer)
        except ValueError:
            raise IOError("HMP40X0: " +
                          "*ESR? command failed (invalid answer [1]).")

        return esr

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
            raise IOError("HMP40X0: *ESR? command failed (no answer).")
        try:
            esr = int(answer)
        except ValueError:
            raise IOError("HMP40X0: " +
                          "*ESR? command failed (invalid answer [1]).")


        self.clear()

        if (esr & 0x20):
            # Command Error. Set when a syntax type error is detected
            # in a command from the bus. The parser is reset and parsing
            # continues at the next byte in the input stream.
            raise PowerSupplyError("HMP40X0: PowerSupply Command Error. " +
                                   "A syntax type error has been detected " +
                                   "in a command from the bus. " +
                                   "The parser has been reset and parsing " +
                                   "continues at the next byte " +
                                   "in the input stream.")

        if (esr & 0x10):
            # Execution Error. Set when an error is encountered while
            # attempting to execute a completely parsed command.
            # The appropriate error number will be redeviceed in 
            # the Execution Error Register

            # Now reading (and clearing) the Execution Error Register

            command = "EER?"
            self.write(command)
            answer = self.read()
            if not(answer):
                raise IOError("HMP40X0: EER? command failed (no answer).")
            try:
                eer = int(answer)
            except ValueError:
                raise IOError("HMP40X0: " +
                              "EER? command failed (invalid answer [1]).")

            if (eer >= 1) and (eer <= 99):
                raise PowerSupplyError("HMP40X0: Hardware error.")

            if eer == 116:
                raise PowerSupplyError("HMP40X0: Invalid recall of data.")

            if eer == 117:
                raise PowerSupplyError("HMP40X0: Corrupted internal data.")

            if eer == 120:
                raise PowerSupplyError("HMP40X0: " +
                              "Numerical specified value was too big " + 
                              "or too small.")

            if eer == 123:
                raise PowerSupplyError("HMP40X0: " +
                              "Illegal recall requested.")

            if eer == 124:
                raise PowerSupplyError("HMP40X0: " +
                              "Illegal range change requested.")


        if (esr & 0x08):
            # Verify Timeout Error. Set when a parameter is set with 'verify'
            # specified and the value is not reached within 5 secs.
            raise PowerSupplyError("HMP40X0: Verify Timeout Error. " +
                          "Set when a parameter is set with 'verify' " +
                          "specified and the value is not reached " +
                          "within 5 secs.")

        if (esr & 0x04):
            # Query Error. Appropriate number is redeviceed in 
            # the Query Error register
            raise PowerSupplyError("HMP40X0: Query Error.")

# ------------------------------------------------------------------ 

    def get_serial(self):
        return self.send("*IDN?")

# ------------------------------------------------------------------ 

    def setup(self, 
              channel = 1, 
              voltage = 1.0, current = 0.1):
        """
        Setup voltage and current for channel 'channel'.
        This command does not activate the output.
        """

        if channel not in self.allchannels:
            raise ValueError("HMP40X0: invalid channel %d" % channel)

        self.reopen_if_needed()
        self.purge()

        self.write("INST:SEL OUT%d" % channel)
        self.check_error_status()
        self.write("SOUR:VOLT %f" % voltage)
        self.check_error_status()
        self.write("SOUR:CURR %f" % current)
        self.check_error_status()


    def enable(self, channel):
        """
        Enable output on channel 'channel'.
        """

        if channel not in self.allchannels:
            raise ValueError("HMP40X0: invalid channel %d" % channel)

        self.reopen_if_needed()
        self.purge()

        self.write("INST:SEL OUT%d" % channel)
        self.check_error_status()
        self.write("OUTP ON")
        self.check_error_status()


    def disable(self, channel):
        """
        Disable output on channel 'channel'.
        """

        if channel not in self.allchannels:
            raise ValueError("HMP40X0: invalid channel %d" % channel)

        self.reopen_if_needed()
        self.purge()

        self.write("INST:SEL OUT%d" % channel)
        self.check_error_status()
        self.write("OUTP OFF")
        self.check_error_status()
        
# ------------------------------------------------------------------

    def measure(self, channel):
        """
        Return voltage (in Volt) and current (in A) for channel 'channel'.
        Return a tuple: (voltage, current).
        """   
        self.reopen_if_needed()
        self.purge()

        self.write("INST:SEL OUT%d" % channel)
        self.check_error_status()
        voltage_str = self.send("MEAS:VOLT?")
        self.check_error_status()
        current_str = self.send("MEAS:CURR?")
        self.check_error_status()

        voltage = float(voltage_str)
        current = float(current_str)

        return (voltage, current)
            
# ------------------------------------------------------------------

    def beep(self, repeat=1):

        self.reopen_if_needed()
        self.purge()

        for i in xrange(repeat):
            self.write("SYST:BEEP")
            time.sleep(.2)

# ==================================================================
