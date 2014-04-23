#! /usr/bin/env python

# ==================================================================
#
# SkyDice
#
# Low level control for the MDrive controller - 
#
# Authors: Laurent Le Guillou & Pier-Francesco Rocci
#
# ==================================================================

import sys
import os, os.path
import time
import serial


# ============ Class Controller ZED =============================================

class MDrive_Z(object):
    """
    The Controller class represents the MicroLynx board.
    """

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 port = '/dev/ttyS1',
                 debug = True):

        self.port = port
        self.baudrate = 9600
        self.rtscts = 0
        self.xonxoff = 0
        # self.timeout = 1.0 # Non-blocking & non waiting mode
        self.timeout = 0.5 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None
        self.EOL = '\r'
    
        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10

    # ---------- Open the controller device ------------------

    def open(self):
        """
        Open the MicroLynx device.
        """
        if self.debug: print >>sys.stderr,  "Opening port %s ..." % self.port
     
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
            raise IOError("MicroLynx: " + 
                          "Failed to open serial port %s" % self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("MicroLynx: " + 
                           "not echoing on serial port %s") % 
                          self.port)
           
        if self.debug: 
            print >>sys.stderr, ( "MicroLynx: Opening port %s done." % 
                                  self.port )
        
        # self.clear()


# ---------- Close the controller device ----------------- 

    def close(self):
 
        if ( self.serial_port and
             self.serial_port.isOpen() ):
            self.serial_port.close()

    # ---------- Define write command  ----------------------- 

    def write(self, command):
        """
        Send a command through the serial port.
        """
        if not( self.serial_port and
                self.serial_port.isOpen() ):
            raise IOError("MicroLynx: " + 
                          "Port %s not yet opened" % self.port)

        if self.debug: print >>sys.stderr, \
                "MicroLynx: Sending command [" + command + "]"
        self.serial_port.write(command + self.EOL)

    # ---------- Define read command  ----------------------- 

    def read(self, timeout = None):
        """
        Read the answer from the serial port.
        Return it as a string.
        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """
        
        if not( self.serial_port and
                self.serial_port.isOpen() ):
            raise IOError("MicroLynx: " + 
                          "Port %s not yet opened" % self.port)

        if self.debug: print >>sys.stderr, "MicroLynx: " + \
                "Reading serial port buffer"

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, "MicroLynx: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.readlines() # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        # answer = answer.strip()
        if self.debug: print >>sys.stderr, "MicroLynx: " + \
                "Received [" + str(answer) + "]"

        return answer

    # ---------- Define purge  ----------------------- 

    def purge(self):
        """
        Purge the serial port to avoid framing errors.
        """
        self.serial_port.flushOutput()
        self.serial_port.flushInput()
        self.serial_port.readlines()

    # ---------- Define read command  ----------------------- 

    def echotest(self):
        self.write("PRINT SER")
        answer = self.read()

        if len(answer) < 1:
            return False

        # TODO Here improve the test

        return True

    # ---------- Send a command and get the answer -----------

    def send(self, cmd):
        """
        Send a command (MicroLynx language) to the motor and
        return the answer (if any).

        @param cmd: the command to send.
        """

        if len(cmd) < 2:
            raise ValueError("Invalid command")

        command = cmd

        # Now send it
        self.write(command)

        # Parsing the answer (to detect errors)

        answer = self.read()

        if len(answer) < 1:
            return answer

        # Detect errors and raise exception if any
        
        # TODO : properly parse the answer here !

        # parts = answer.split()
        # if len(parts) > 1:
        #     if parts[0][0] == '?':  # An error occured
        #         # if error ("?") -> raise Exception
        #         raise MCAPIError(int(parts[0][1:]))

        # Remove the useless prompt '>' (not always present)

        if answer[-1] == '>':
            answer = answer[:-1]

        return answer


    # ---------- Setup the motors ----------------------------

    def setup(self, minimal = False):
        """
        Initialize the controller board.
        Disable ECHO.
        Configure each connected motor (init strings)
        """
        # Disable ECHO MODE

        answer = self.send("ECHO=1")

        if not(minimal):
            self.send('ACCL=25000')
            self.send('DECL=25000')
            self.send('VI=1000')
            self.send('VM=50000')
      
        # Here we need a check !

    # ---------- Current motor position ---------------------- 

    def get_position(self):
        """
        Return the current axis position.
        """
        answer = self.send('PRINT POS')

        if len(answer) < 1:
            raise IOError(("MicroLynx: " + 
                           "not responding to PRINT POS on serial port %s") % 
                          self.port)
        
        position = float(answer[0])
        return position


    # ---------- Move absolute and relative ------------------ 

    def is_moving(self):
        answer = self.send("PRINT MVG")
        if len(answer) < 1:
            raise IOError(("MicroLynx: " + 
                           "not responding to PRINT MVG on serial port %s") % 
                          self.port)
        answer = answer[0].strip()
        if answer == 'TRUE':
            return True
        else:
            return False
        

    def move_absolute(self, position, wait=True):
        """
        Move the axis to absolute position 'position'.
        @param position: target position.
        """

        # Here add a limit check on the position ?

        command = "MOVA %f" % position
        answer = self.send(command)
        # in ECHO=1 no answer []

        if wait:
            while (self.is_moving()):
                pass


    def move_relative(self, offset, wait = True):
        """
        Move the axis of relative offset 'offset'.
        @param offset: position offset (positive or negative)
        """
        command = "MOVR %f" % offset
        answer = self.send(command)
        # in ECHO=1 no answer []

        if wait:
            while (self.is_moving()):
                pass

# =========================================================
