#! /usr/bin/env python

# ==================================================================
#
# Pollux Motors control commands
#
# Authors: Laurent Le Guillou & Pier-Francesco Rocci & Remy Le Breton
#
# ==================================================================

import sys
import os, os.path
import time
import serial


# ============ Class Controller ZED =============================================

class Pollux_motor(object):
    """
    The Controller class represents the Pollux board.
    """

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 port = '/dev/ttyUSB0',
                 debug = True):

        self.port = port
        self.baudrate = 19200
        # self.timeout = 1.0 # Non-blocking & non waiting mode
        self.timeout = 0.5 # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None
        self.EOL = '\n'
    
        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10

        # ---- default axis
        self.axis = "1"

    # ---------- Open the controller device ------------------

    def open(self):
        """
        Open the Pollux device.
        """
        if self.debug: print >>sys.stderr,  "Opening port %s ..." % self.port
     
        self.serial_port = serial.Serial(port = self.port, 
                                         baudrate = self.baudrate,
                                         bytesize = self.bytesize, 
                                         parity = self.parity,
                                         stopbits = self.stopbits, 
                                         timeout = self.timeout)
        
        if ( (self.serial_port == None) or
             not(self.serial_port.isOpen()) ):
            raise IOError("Failed to open serial port %s" % self.port)
        
        self.serial_port.flushOutput()
        
        if not(self.echotest()):
            raise IOError(("Not echoing on serial port %s") % 
                          self.port)
           
        if self.debug: 
            print >>sys.stderr, ( "Opening port %s done." % 
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
            raise IOError("Port %s not yet opened" % self.port)

        if self.debug: print >>sys.stderr, \
                "Sending command [" + command + "]"
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
            raise IOError("Port %s not yet opened" % self.port)

        if self.debug: print >>sys.stderr, \
                "Reading serial port buffer"

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.readlines() # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        # answer = answer.strip()
        if self.debug: print >>sys.stderr, \
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
        self.write(self.axis + " getserialno")
        answer = self.read()

        if len(answer) < 1:
            return False

        return True

    # ---------- Send a command and get the answer -----------

    def send(self, cmd):
        """
        Send a command (Venus-2 language) to the motor and
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

        if not(minimal):
            self.send('0.5 ' + self.axis + ' snv')
            self.send('0.5 ' + self.axis + ' sna')
            self.send('500.0 ' + self.axis + ' setnstopdecel')
            self.send('0.5 ' + self.axis + ' setcalvel')
            self.send('0.5 ' + self.axis + ' setnrmvel')
            self.send('0.5 ' + self.axis + ' setnrefvel')

    # ---------- Current motor position ---------------------- 

    def get_position(self):
        """
        Return the current axis position.
        """
        answer = self.send(self.axis + " np")

        if len(answer) < 1:
            raise IOError(("Not responding to " + self.axis + " np on serial port %s") % 
                          self.port)
        
        position = float(answer[0])
        return position

    position = property(get_position, doc="Axis current position")

    # ---------- Move absolute and relative ------------------ 

    def is_moving(self):
        answer = self.send(self.axis + " nst")
        if len(answer) < 1:
            raise IOError(("Not responding to 1 nst on serial port %s") % 
                          self.port)
        answer = answer[0].strip()
        if answer == '1':
            return True
        else:
            return False
        

    def move_absolute(self, position, wait=True, check = False):
        """
        Move the axis to absolute position 'position'.
        @param position: target position.
        @param check: to take into account the limits of the range, if False, move without constraints.
        """
        
        if check == False:
            command = ("%f " + self.axis + " nm") % position
            answer = self.send(command)
            # in ECHO=1 no answer []

            if wait:
                while (self.is_moving()):
                    pass

        if check == True:
            if (len(self._Pollux_motor__limits['down']) < 1) or (len(self._Pollux_motor__limits['up']) < 1):
                raise ValueError ("There are no limits to check. \n Please do find_limits before.")
            else:
                if (position < self._Pollux_motor__limits['up']) and (position > self._Pollux_motor__limits['down']) : 
                    command = ("%f " + self.axis + " nm") % position
                    answer = self.send(command)
                    # in ECHO=1 no answer []
                
                    if wait:
                        while (self.is_moving()):
                            pass
                else:
                    raise ValueError ("You have chosen a position outside of the range.")

    def move_relative(self, offset, wait = True, check = False):
        """
        Move the axis of relative offset 'offset'.
        @param offset: position offset (positive or negative)
        @param check: to take into account the limits of the range. If False, move without constraints.
        """

        if check == False:
            command = ("%f " + self.axis + " nr") % offset
            answer = self.send(command)
            # in ECHO=1 no answer []
            
            if wait:
                while (self.is_moving()):
                    pass

        if check == True:
            if (len(self._Pollux_motor__limits['down']) < 1) or (len(self._Pollux_motor__limits['up']) < 1):
                raise ValueError ("There are no limits to check. \n Please do find_limits before.")
            else:
                get_position(self)
                if (self.position + offset < self._Pollux_motor__limits['up']) and (self.position + offset > self._Pollux_motor__limits['down']) : 
                    command = ("%f " + self.axis + " nr") % offset
                    answer = self.send(command)
                    # in ECHO=1 no answer []
                
                    if wait:
                        while (self.is_moving()):
                            pass
                else:
                    raise ValueError ("You have chosen a position outside of the range.")

    # =========================================================

    # Adapted from SkyDice motors
    
    # ---------- Detect limits (range) -------------------------- 

    def find_limits(self, up = True, down = True):
        """
        Pollux motors is supposed to find its limits on its own,
        using calibrate (lower limit, set to zero after calibration) and
        using range (find the range, so the upper limit)

        When power-on for the first time, default zero position is the actual position

        Then it goes to the middle of the axis
        """

        limits = {}

        if down:
            command = self.axis + " ncal"
            answer = self.send(command)
            
            while (self.is_moving()): 
                pass
            
            limits['down'] = self.position

        if up:
            command = self.axis + " nrm"
            answer = self.send(command)
            
            while (self.is_moving()): 
                pass
            
            limits['up'] = self.position

        self.__limits = dict(limits)
        
        return limits

    # ---------- Set zero at the current position ------------ 

    def set_zero(self, position=0):
        """
        Define the current position of the motor to be 'position'. 
        From then on, all positions reported for that motor will
        be relative to that point.

        @param position: new value for the current position.
        """
       
        command = "%d " + self.axis + " setnpos" % position
        answer = self.send(command)

    # ---------- Home : find_limits and set zeros ------------ 

    def home(self):
        """
        Look for the limits (find_limits()), move the motor
        to the middle position, and then set the zero there.

        Please use this procedure instead of find_limits()
        """
        limits = self.find_limits(up = True, down = True)
        # use the middle point as zero
        middle = (limits['up'] + limits['down'])/2.0
        offset = middle
        self.move_absolute(offset, wait = True, check = False)
        self.set_zero()

        for k in ['up', 'down']:
            if self.__limits.has_key(k):
                self.__limits[k] -= offset # subtract the offset


    # ---------- Return limits ------------------------------- 

    def get_limits(self):
        return self.__limits

    def check_limits(self, position):
        if self.__limits.has_key('up'):
            if position >= self.__limits['up']:
                return False

        if self.__limits.has_key('down'):
            if position <= self.__limits['down']:
                return False

        return True

