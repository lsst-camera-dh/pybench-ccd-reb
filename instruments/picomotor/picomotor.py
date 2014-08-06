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
                 host = "134.158.154.199",
                 port = 23, 
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

        # --- moves memory 

        self.moves = {}

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

        key = (driver,channel)
        if not(self.moves.has_key(key)):
            self.moves[key] = 0
        self.moves[key] += offset

        ## TODO : check errors


    # ---------- Move absolute and relative ------------------ 

    def is_moving(self, driver):
        # TODO: Adapt this
        # send : STA <driver>
        # analyze status bit mask
        
        

        answer = self.send(("%d" % self.axis) + " nst")
        if len(answer) < 1:
            raise IOError(("Not responding to 1 nst on serial port %s") % 
                          self.port)
        answer = answer[0].strip()
        if answer == '1':
            return True
        else:
            return False
        


    # =========================================================


# ===================================================================
