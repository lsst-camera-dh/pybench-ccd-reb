#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

# ==================================================================
#
# SkyDice
#
# Low level control for the PowerSupply - TTiQL355TP
#
# Authors: Laurent Le Guillou & Pier-Francesco Rocci
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

class PowerSupply:

# ------------------------------------------------------------------ 
    
    def __init__(self, 
                 port = '/dev/ttyUSB-TTiQL355TP', # defined by udev rules
                 debug = True):
        """
        Create a PowerSupply instance.
        """
        
        # ---- Serial port configuration ------
        self.port = port
        self.baudrate = 19200
        self.echo = 0
        self.rtscts = 0
        self.xonxoff = 0
        self.timeout = 1 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None

        self.EOL = '\n'              # = LF end of line EOL
        self.answer_EOL = '\r\n'     # EOL in Supply answers

        # ---- existing channels
        # self.allowed_channels = [1, 2, 3] # 3 is auxiliary ???
        self.allowed_channels = [1, 2, 3] # 3 is auxiliary ???

        # ---- allowed voltage/current ranges
        self.allowed_intervals_description = {0: '15V/5A',
                                              1: '35V/3A',
                                              2: '35V/500mA'}
        self.allowed_intervals = self.allowed_intervals_description.keys()
        
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

        if self.debug: print "Opening port %s ..." % self.port
        
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
            raise IOError("TTiQL355TP: Failed to open serial port %s" % 
                          self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError( "TTiQL355TP: " +
                          ( "PowerSupply is not echoing on serial port %s" % 
                            self.port ) )
        
        
        if self.debug: 
            print >>sys.stderr, "TTiQL355TP: Opening port %s done." % self.port

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
           
    # def wait_answer(self, timeout):
    #     """
    #     Wait for reading line on serial port with a different timeout. 
    #     Return the line.
    #     """

    #     self.serial_port.timeout = timeout
    #     answer = self.serial_port.readline()
    #     self.serial_port.timeout = self.timeout # restore timeout
    #     return answer
 
# ------------------------------------------------------------------ 

    def reopen_if_needed(self):
        """
        Reopen the serial port if needed.
        """
        if not(self.serial_port):
            raise IOError("TTiQL355TP: " +
                          "PowerSupply serial port should be opened first.")

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
                "TTiQL355TP: Sending command [" + command + "]"
        self.serial_port.write(command + self.EOL)


    def read(self):
        """
        Read the answer from the serial port.
        Return it as a string.
        """
        if self.debug: print >>sys.stderr, "TTiQL355TP: " + \
                "Reading serial port buffer"
        answer = self.serial_port.readline() # return buffer
        answer = answer.strip()
        if self.debug: print >>sys.stderr, "TTiQL355TP: " + \
                "Received [" + answer + "]"

        return answer

# ------------------------------------------------------------------ 

    def echotest(self):
        """
        Verify communications with the PowerSupply.
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

        command = "*RST"
        self.write(command)

# ------------------------------------------------------------------ 
        
    def clear(self):
        """
        Clear the Powersupply status.
        """ 
        self.reopen_if_needed()
        self.purge()

        if self.debug: print >>sys.stderr, "Clear Status registers"
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

        command = "*ESR?"
        self.write(command)
        answer = self.read()
        if not(answer):
            raise IOError("TTiQL355TP: *ESR? command failed (no answer).")
        try:
            esr = int(answer)
        except ValueError:
            raise IOError("TTiQL355TP: " +
                          "*ESR? command failed (invalid answer [1]).")

        if (esr & 0x20):
            # Command Error. Set when a syntax type error is detected
            # in a command from the bus. The parser is reset and parsing
            # continues at the next byte in the input stream.
            raise PowerSupplyError("TTiQL355TP: PowerSupply Command Error. " +
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
                raise IOError("TTiQL355TP: EER? command failed (no answer).")
            try:
                eer = int(answer)
            except ValueError:
                raise IOError("TTiQL355TP: " +
                              "EER? command failed (invalid answer [1]).")

            if (eer >= 1) and (eer <= 99):
                raise PowerSupplyError("TTiQL355TP: Hardware error.")

            if eer == 116:
                raise PowerSupplyError("TTiQL355TP: Invalid recall of data.")

            if eer == 117:
                raise PowerSupplyError("TTiQL355TP: Corrupted internal data.")

            if eer == 120:
                raise PowerSupplyError("TTiQL355TP: " +
                              "Numerical specified value was too big " + 
                              "or too small.")

            if eer == 123:
                raise PowerSupplyError("TTiQL355TP: " +
                              "Illegal recall requested.")

            if eer == 124:
                raise PowerSupplyError("TTiQL355TP: " +
                              "Illegal range change requested.")


        if (esr & 0x08):
            # Verify Timeout Error. Set when a parameter is set with 'verify'
            # specified and the value is not reached within 5 secs.
            raise PowerSupplyError("TTiQL355TP: Verify Timeout Error. " +
                          "Set when a parameter is set with 'verify' " +
                          "specified and the value is not reached " +
                          "within 5 secs.")

        if (esr & 0x04):
            # Query Error. Appropriate number is reported in 
            # the Query Error register
            raise PowerSupplyError("TTiQL355TP: Query Error.")

# ------------------------------------------------------------------ 

    def set_range(self, channel, interval):
        """
        Set the range of channel <channel> for powerSupply to the <interval>.
        """
        
        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")
        
        if (interval not in self.allowed_intervals):
            raise ValueError("Range ", interval, "is not available.")

        self.reopen_if_needed()
        self.purge()

        command = 'RANGE'+ str(channel) + ' ' + str(interval)
        self.write(command)

        # Check for errors

        self.check_error_status()

# ------------------------------------------------------------------

    def get_range(self, channel):
        """
        Get the range of channel <channel>.
        """
        
        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")

        self.reopen_if_needed()
        self.purge()

        command = 'RANGE'+ str(channel) + '?' 
        self.write(command)

        answer = self.read()

        self.check_error_status()
        
        # Expected syntax: "R1 1"   i.e. R<channel> <interval>

        if len(answer) < 4:
            raise IOError("RANGE? command failed (incomplete answer).")

        if answer[0] != 'R':
            raise IOError("RANGE? command failed (invalid answer [1]).")

        elts = answer[1:].split()
        if len(elts) != 2:
            raise IOError("RANGE? command failed (invalid answer [2]).")

        try:
            ch = int(elts[0])
            rr = int(elts[1])
        except ValueError:
            raise IOError("RANGE? command failed (invalid answer [3]).")

        if ch not in self.allowed_channels:
            raise IOError("RANGE? command failed (invalid answer [4]).")

        if rr not in self.allowed_intervals:
            raise IOError("RANGE? command failed (invalid answer [5]).")

        return rr
        
# ------------------------------------------------------------------

    def set_V(self, channel, voltage):
        """
        Set the Voltage value for channel <channel>.
        """

        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")
        
        self.reopen_if_needed()
        self.purge()

        command = 'V'+ str(channel) + ' ' + str(voltage)
        self.write(command)

        self.check_error_status()

# ------------------------------------------------------------------

    def set_I(self, channel, current):
        """
        Set the Maximum Current value for channel <channel>.
        """

        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")

        self.reopen_if_needed()
        self.purge()

        command = 'I'+ str(channel) + ' ' + str(current)
        self.write(command)

        self.check_error_status()
           
# ------------------------------------------------------------------

    def on(self, channel):
        """
        Turn ON power on channel <channel>. All channels
        will be turned on if you specify 'all'.
        """
        if (channel == 'all'):
            self.set_opall(True)
            return

        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")

        self.set_op(channel, True)



    def off(self, channel):
        """
        Turn OFF power on channel <channel>. All channels
        will be turned off if you specify 'all'.
        """
        if (channel == 'all'):
            self.set_opall(False)
            return

        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")

        self.set_op(channel, False)


    def set_op(self, channel, turn_on = True):
        """
        Turn on/off output on channel <channel>.
        """

        if (channel not in self.allowed_channels):
            raise ValueError("Channel ", channel, "is not available.")

        nrf = 0
        if turn_on:
            nrf = 1

        self.reopen_if_needed()
        self.purge()

        command = 'OP'+ str(channel) + ' ' + str(nrf)
        self.write(command)

        self.check_error_status()


    def set_opall(self, turn_on):
        """
        Turn on/off output on all channels
        """
        nrf = 0
        if turn_on:
            nrf = 1

        self.reopen_if_needed()
        self.purge()

        command = 'OPALL' + ' ' + str(nrf)
        self.write(command)

        self.check_error_status()

# ------------------------------------------------------------------

#     def set_mode(self, nrf):
#         """
#         set the instruments operating mode.
#         """
#         if nrf not in [0,1,2]: 
#             raise IOError("Attention values out of range!")
        
#         if not(self.serial_port): 
#             raise IOError("PowerSupply serial port should be opened first.")
        
#         if not(self.serial_port.isOpen()): 
#             self.open()
        
#         self.serial_port.flushOutput()
#         self.serial_port.flushInput()
        
#         if self.debug: print >>sys.stderr, "Sending Command MODE"
#         self.serial_port.write('MODE '+ str(nrf) + self.EOL)
        
#         if self.debug: print >>sys.stderr, "Wait..."
#         self.serial_port.write('*WAI' + self.EOL)
        
#         self.serial_port.write('EER?'+ self.EOL)
#         error = self.serial_port.readline() # return buffer
#         if self.debug: print >>sys.stderr, "Error: ", error
#         if not(error): 
#             raise IOError("Error! Check error register.")

# # ------------------------------------------------------------------


#     def get_mode(self):
#         """
#         get the instruments operating mode.
#         """
#         if not(self.serial_port):
#             raise IOError("PowerSupply serial port should be opened first.")

#         if not(self.serial_port.isOpen()): # open if port is closed
#             self.open()

#         self.serial_port.flushOutput()
#         self.serial_port.flushInput()

#         if self.debug: print >>sys.stderr, "Sending Command MODE?"
#         self.serial_port.write('MODE?' + self.EOL)
    
#         if self.debug: print >>sys.stderr, "Wait..."
#         self.serial_port.write('*WAI' + self.EOL)

#         if self.debug: print >>sys.stderr, "Reading buffer"
#         answer = self.serial_port.readline() # return buffer
#         if self.debug: print >>sys.stderr, "Received [", answer, "]"

#         if not(answer):
#             raise IOError("MODE? command failed.")


# ------------------------------------------------------------------

    # def inc_V(self, n):
    #     """
    #     increment the output <n> by the step.
    #     """ 

# ------------------------------------------------------------------


    # def dec_V(self, n):
    #     """
    #     decrement the output <n> by the step.
    #     """ 

# ------------------------------------------------------------------

    # def delta_V(self, n, step, verify):
    #     """
    #     set the output <n> voltage step size.
    #     """ 

# ------------------------------------------------------------------


    # def delta_I(self, n, step, verify):
    #     """
    #     set the output <n> input step size.
    #     """ 

# ------------------------------------------------------------------


    # def inc_I(self, n):
    #     """
    #     increment the output <n> by the step.
    #     """

# ------------------------------------------------------------------


    # def dec_I(self, n):
    #     """
    #     decrement the output <n> by the step.
    #     """


# ==================================================================
