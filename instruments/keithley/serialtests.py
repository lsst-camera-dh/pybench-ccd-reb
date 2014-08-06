#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# ======================================================================
#
# SkyDice
#
# Low level control for the Keithley multimeter through 
#
# Author: Laurent Le Guillou <llg@lpnhe.in2p3.fr>
#
# ======================================================================


import os
import os.path
import getopt
import sys
import time
import datetime
import serial
import math


# ======================================================================

# ---- Serial port configuration ------

# port = "/dev/ttyS0"
port = "/dev/ttyS3"
baudrate = 9600
echo = 0
rtscts = 0
xonxoff = 0
timeout = 0.5 # Non-blocking & non waiting mode
repr_mode = 0
parity = serial.PARITY_NONE
bytesize = serial.EIGHTBITS
stopbits = serial.STOPBITS_ONE

# ---- open the port ------------------
try:
    serial_port = serial.Serial(port=port, baudrate=baudrate,
                                rtscts=rtscts, xonxoff=xonxoff,
                                bytesize=bytesize, parity=parity,
                                stopbits=stopbits, timeout=timeout)


except:
    error("Could not open port " + str(port) + ". Stop.")
    sys.exit(1)
        

  #  serial_port.write("*CLS")
  #  serial_port.write("*RST")
  #  serial_port.write("DISP:ENAB OFF")

# ---- Flush output (in case)

#serial_port.flushOutput()

# ---- Reset default

# serial_port.write(str(bytearray([27])))

# answer = serial_port.readline()

# print repr(answer)

# ======================================================================
