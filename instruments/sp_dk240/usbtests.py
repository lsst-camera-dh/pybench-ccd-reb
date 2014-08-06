#! /usr/bin/env python
# -*- Encoding: utf-8 -*-

import sys
import os, os.path

import serial

# ---- Serial port configuration ------

# port="/dev/ttyS0"
port = "/dev/ttyUSB0"
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

# ---- Flush output (in case)

serial_port.flushOutput()

    # # ---- Ask for the station 'address' --

    # serial_port.write('?' + '\r\n')
    # address = serial_port.readline()
    # if not(address):
    #     print >>sys.stderr, "WXT510 meteo station connection failed."
    #     sys.exit(2)
    # address = address.strip()


    # serial_port.flushOutput()
    # serial_port.write(address + 'R' + '\r\n')
    # answer_lines = serial_port.readlines(eol='\r\n')
    # answer = '\r\n'.join(answer_lines)


# serial_port.write("*IDN?\n")
# serial_port.readline()

# serial_port.write("*TST?\n")
# serial_port.readline()

# serial_port.write("*OPC?\n")
# serial_port.readline()

# serial_port.write("RANGE2?\n")
# serial_port.readline()
# serial_port.write("RANGE1?\n")
# serial_port.readline()

# serial_port.write("RANGE1 2\n")
# serial_port.write("RANGE1 0\n")

# serial_port.write("INCV1\n")

# serial_port.write("EER?\n")
# serial_port.readline()

# serial_port.write("EER?\n")
# serial_port.readline()

# serial_port.write("*IDN?\n")
# serial_port.readline()

# serial_port.write("V1?\n")
# serial_port.readline()

# serial_port.write("V2?\n")
# serial_port.readline()

# serial_port.write("I1?\n")
# serial_port.readline()

# serial_port.write("I2?\n")
# serial_port.readline()

# serial_port.write("I1 0.330\n")
# serial_port.write("I1 0.430\n")
# serial_port.write("I1 0.530\n")
# serial_port.write("V1 0.530\n")
# serial_port.write("I1 6\n")
# serial_port.readline()
# serial_port.write("EER?\n")
# serial_port.readline()
# serial_port.write("EER?\n")
# serial_port.readline()

# serial_port.write("OP2 1\n")
# serial_port.write("OP2 0\n")

# serial_port.write("OPALL 1\n")
# serial_port.write("OPALL 0\n")

# serial_port.write("MODE 1\n")
# serial_port.write("MODE?\n")
# serial_port.write("LOCAL\n")

# serial_port.write("*IDN?\n")
# serial_port.readline()

# serial_port.write("DELTAV1 0.01\n")
# serial_port.readline()

# serial_port.write("INCV1\n")
# serial_port.readline()

# serial_port.write("OPALL 1\n")
# serial_port.readline()

# serial_port.write("V1 13.;V2 13.0;OPALL 0\n")
