#! /usr/bin/env python

# ==================================================================
#
# LSST
#
# New Focus Picomotor Controller
#
# Author: Laurent Le Guillou
#
# ==================================================================

import sys
import os, os.path
import time
# import serial
import telnetlib


# ============ Class Pollux controller ==============================

class Picomotor(object):
    """
    The Controller class represents the Picomotor controller.
    """

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 host = None,
                 port = None, # either TCP/IP or serial one
                 debug = True):

        # self.serial_conn = None
        self.tcp_conn = None
        self.host = host
        self.port = port
        if self.port == None:
            self.port = 23

        self.timeout = 0.5 # Non-blocking & non waiting mode

        self.EOL = '\n'
    
        # ---- debug mode
        self.debug = debug

    # ---------- Open the controller device ------------------

    def open(self):
        """
        Open the Picomotor controller device.
        Check if there's something connected (echotest).
        """

        if self.debug: 
            print >>sys.stderr,  "Opening host %s:%d ..." % (self.host,
                                                             self.port)
     
        # self.tcp_conn = telnetlib.Telnet(host = self.host, 
        #                                  port = self.port, 
        #                                  timeout = self.timeout)
        # DO NOT PROVIDE host / port / etc 
        # when you create the Telnet instance
        # -> bug: does not work
            
        self.tcp_conn = telnetlib.Telnet()
        self.tcp_conn.open(host = self.host, port = self.port, 
                           timeout = self.timeout)

        time.sleep(1)

        self.purge()

        time.sleep(1)

        if not(self.echotest()):
            raise IOError(("Not echoing on TCP/IP %s:%s") % 
                          (self.host, self.port))
           
        if self.debug: 
            print >>sys.stderr, ( "Opening socket %s:%s done." % 
                                  (self.host, self.port))

        
    # ---------- Close the controller device ----------------- 

    def close(self):
 
        self.tcp_conn.close()

    # ---------- Define write command  ----------------------- 

    def write(self, command):
        """
        Send a command through the serial port.
        """
        if self.debug: print >>sys.stderr, \
                "Sending command [" + command + "]"
        self.tcp_conn.write(command + self.EOL)

    # ---------- Define read command  ----------------------- 

    def read(self):
        """
        Read the answer from the tcp/ip socket
        Return it as a string.
        """
        
        if self.debug: 
            print >>sys.stderr, "Reading tcp/ip socket"

            
        answer = ""
        
        resp = self.tcp_conn.read_very_eager()
        while (resp != ''):
            answer += resp
            resp = self.tcp_conn.read_very_eager()
            

        if self.debug: print >>sys.stderr, \
                "Received [" + str(answer) + "]"

        return answer

    # ---------- Define purge  ----------------------- 

    def purge(self):
        """
        Purge the serial port / telnet socket to avoid framing errors.
        """
        self.read()

    # ---------- Define read command  ----------------------- 

    def echotest(self):
        self.write("VER" + self.EOL)
        time.sleep(0.5)
        answer = self.read()

        print "ANSWER = ", answer

        if len(answer) < 1:
            return False

        return True

    # ---------- Send a command and get the answer -----------

    def send(self, cmd):
        """
        Send a command (picomotor language) to the motor and
        return the answer (if any).

        @param cmd: the command to send.
        """

        if len(cmd) < 2:
            raise ValueError("Invalid command")

        command = cmd

        # Now send it
        self.write(command)

        time.sleep(0.5)

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

    def setup(self):
        """
        Initialize the controller. 
        Setup the speed and accelerations.
        """

        pass

        # self.send('1.0 '   + ("%d" % self.axis) + ' snv')
        # self.send('1.0 '   + ("%d" % self.axis) + ' sna')
        # self.send('500.0 ' + ("%d" % self.axis) + ' setnstopdecel')
        # # self.send('1.0 '   + ("%d" % self.axis) + ' setcalvel')
        # # self.send('1.0 '   + ("%d" % self.axis) + ' setnrmvel')
        # self.send('1.0 '   + ("%d" % self.axis) + ' setnrefvel')

    # ---------- Get Error status ---------------------------- 


    # ---------- Is the motor moving ? ----------------------- 




    # ---------- Detect the motors --------------------------- 


    # ---------- Select channel for a driver ----------------- 

    def select(self, driver, channel):
        command = "CHL %s=%d" % (driver, channel)
        answer = self.send(command)

        ## TODO : check errors

    # ---------- Get the selected channels ------------------- 

    def get_selected(self, driver):
        command = "CHL %s" % driver
        answer = self.send(command)

        channel = int(answer.strip())
        return channel

    # ---------- Move the chosen motor ----------------------- 

    def move(self, driver, channel, offset, immediate = True):
        self.select(driver, channel)
        
        command = "REL %s %d" % (driver, offset)
        if immediate:
            command += " G"

        self.send(command)

        ## TODO : check errors


    # ---------- Current motor position ---------------------- 

    def get_position(self):
        """
        Return the current axis position.
        """
        answer = self.send(("%d" % self.axis) + " np")

        if len(answer) < 1:
            raise IOError(("Not responding to " + ("%d" % self.axis) + " np on serial port %s") % 
                          self.port)
        
        position = float(answer[0])
        return position

    position = property(get_position, doc="Axis current position")

    # ---------- Move absolute and relative ------------------ 

    def is_moving(self):
        answer = self.send(("%d" % self.axis) + " nst")
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
        @param wait: control is returned only when the movement is finished.
        @param check: to take into account the limits of the range, if False, move without constraints.
        """
        
        if check and self.__limits:
            # Limits are already known so we can check
            if ( (position < self.__limits['down']) or 
                 (position > self.__limits['up']) ):
                raise ValueError("Invalid position (out of range)")

        command = ("%f" % position) + " " + ("%d" % self.axis) + " nm"
        answer = self.send(command)
        # in ECHO=1 no answer []

        if wait:
            while (self.is_moving()):
                pass



    def move_relative(self, offset, wait = True, check = False):
        """
        Move the axis of relative offset 'offset'.
        @param offset: position offset (positive or negative)
        @param check: to take into account the limits of the range. If False, move without constraints.
        """

        if check and self.__limits:
            target = self.get_position() + offset
            # Limits are already known so we can check
            if ( (target < self.__limits['down']) or 
                 (target > self.__limits['up']) ):
                raise ValueError("Invalid position (out of range)")

        command = ("%f" % offset) + " " + ("%d" % self.axis) + " nr"
        answer = self.send(command)
        # in ECHO=1 no answer []

        if wait:
            while (self.is_moving()):
                pass


    # =========================================================

    # Adapted from SkyDice motors
    
    # ---------- Detect limits (range) -------------------------- 

    def find_limits(self):
        """
        Pollux motors is supposed to find its limits on its own,
        using calibrate command (lower limit, set to zero after calibration) 
        and using range (find the range, so the upper limit).

        When power-on for the first time, the actual position
        is thought to be zero, whatever the position is.
        """

        self.__limits = {}

        # first look for the lower limit (and set that position to zero)

        command = ("%d" % self.axis) + " ncal"
        answer = self.send(command)
        while (self.is_moving()): 
            pass
            
        self.__limits['down'] = self.position  # zero in fact

        # then look for the upper limit 

        command = ("%d" % self.axis) + " nrm"
        answer = self.send(command)
        while (self.is_moving()): 
            pass
            
        self.__limits['up'] = self.position

        return self.__limits

    # ---------- Set zero at the current position ------------ 

    def set_zero(self, position = 0):
        """
        Define the current position of the motor to be 'position'. 
        From then on, all positions reported for that motor will
        be relative to that point.

        @param position: new value for the current position.
        """
       
        command = ("%f" % float(position)) + " " + ("%d" % self.axis) + " setnpos" 
        answer = self.send(command)

    # ---------- Home : find_limits and set zeros ------------ 

    def home(self):
        """
        Look for the limits (find_limits()), move the motor
        to the middle position, and then set the zero there.

        Please use this procedure instead of find_limits().
        """
        limits = self.find_limits()
        # use the middle point as zero
        middle = (limits['up'] + limits['down'])/2.0
        self.move_absolute(middle, wait = True, check = False)
        self.set_zero()

        for k in ['up', 'down']:
            if self.__limits.has_key(k):
                self.__limits[k] -= middle # subtract the offset


    # ---------- Return limits ------------------------------- 

    def get_limits(self):
        return self.__limits

    # def check_limits(self, position):
    #     if self.__limits.has_key('up'):
    #         if position > self.__limits['up']:
    #             return False

    #     if self.__limits.has_key('down'):
    #         if position < self.__limits['down']:
    #             return False

    #     return True

# ===================================================================
