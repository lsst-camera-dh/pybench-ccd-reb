#!/usr/bin/python
# -*- encoding: utf-8 -*-

# ======================================================================
#
# SkyDice
#
# Low level control for the Monochromator SP DK240
#
# Authors: L. Le Guillou & P.-F. Rocci 
# Email: <llg@lpnhe.in2p3.fr>, <procci@lpnhe.in2p3.fr>
#
# ======================================================================


import sys
import os, os.path
import time
import datetime
import serial


# ======================================================================

def int2bytes(value):
    """
    Convert an integer in range [0-65535] to its 2-byte representation.
    """
    #
    value = int(value)
    #
    if (value < 0) or (value > 0xffff):
        raise ValueError("Invalid parameter value. Should be in [0-65535].")
    #
    low_byte  = ( value & 0x00ff )
    high_byte = ( value & 0xff00 ) / 0x100
    #
    return high_byte, low_byte


def bytes2int(high_byte, low_byte):
    """
    Convert 2 bytes into an integer in range [0-65535].
    """
    #
    return 0x100 * high_byte + low_byte


def int3bytes(value):
    """
    Convert an integer in range [0-1048575] to its 3-byte representation.
    """
    #
    value = int(value)
    #
    if (value < 0) or (value > 0xffffff):
        raise ValueError("Invalid parameter value. Should be in [0-1048575].")
    #
    low_byte    = ( value & 0x0000ff )
    middle_byte = ( value & 0x00ff00 ) / 0x100
    high_byte   = ( value & 0xff0000 ) / 0x10000
    #
    return high_byte, middle_byte, low_byte


def bytes3int(high_byte, middle_byte, low_byte):
    """
    Convert 3 bytes into an integer in range [0-1048575].
    """
    #
    return 0x10000 * high_byte + 0x100 * middle_byte + low_byte


# ======================================================================

class Monochromator:

    # ------------------------------------------------------------------

    END_OF_ANSWER = 0x18      # 24 endmark of answers.
    # EOL = '\r\n'              # EOL (IS THERE ANY ???????????? )

    # ------------------------------------------------------------------

    def __init__(self, 
                 port = '/dev/ttyS0',
                 debug = True):
        """
        Create a SP DK 240 monochromator instance.
        """

        # ---- Serial port configuration ------
        self.port = port
        self.baudrate = 9600
        self.echo = 0
        self.rtscts = 0
        self.xonxoff = 0
        self.timeout = 1. # Non-blocking & non waiting mode
        self.repr_mode = 0
        self.parity = serial.PARITY_NONE
        self.bytesize = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.serial_port = None

        # ---- debug mode
        self.debug = debug

        # ---- action timeout 
        self.action_timeout = 10

        # Operation time 38.5s from 10 to 3000 micron for both slits
        self.both_slits_adjust_timeout = 50   # measured: 38.5s

        # Operation time 12.8s from 10 to 3000 micron for one slit
        self.one_slit_adjust_timeout = 20   # measured: 12.8s

        # Operation time 38.1s from 200 nm to 1000 nm (grating #3)
        self.set_wavelength_timeout = 50    # measured 38.1s

        # Operation time 114s to change from grating #1 to #3
        self.set_grating_timeout = 150

    # ------------------------------------------------------------------

    def open(self):
        """
        Open and initialize the serial port to communicate
        with the monochromator.
        """
        # ---- open the port ------------------

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
                 raise IOError("Failed to open serial port %s" % self.port)

        self.serial_port.flushOutput()

        if not(self.echotest()):
                 raise IOError("Monochromator is not echoing on serial port %s" % self.port)
            

        if self.debug: 
            print "Opening port %s done." % self.port
        

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
            raise IOError("SP DK240: " +
                          "Monochromator serial port should be opened first.")

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
#

    def write(self, command):
        """
        Send a command through the serial port.
        """
        if self.debug: print >>sys.stderr, \
                "SP DK240: Sending command [", \
                list(bytearray(command)), "]"
        self.serial_port.write(command)


    def read(self, nbytes, timeout = None):
        """
        Read nbytes from the serial port. Return them as a string.

        If <timeout> is specified, the function will wait for data 
        with the specified timeout (instead of the default one). 
        """
        
        if self.debug: print >>sys.stderr, "SP DK240: " + \
                "Reading %d byte(s) on serial port" % nbytes

        if timeout != None:
            self.serial_port.timeout = timeout
            if self.debug: print >>sys.stderr, "SP DK240: " + \
                    "Timeout specified: ", timeout
            
        answer = self.serial_port.read(nbytes) # return buffer
        
        # Restoring timeout to default one
        self.serial_port.timeout = self.timeout
        
        # removing end of line should not be done here !

        if self.debug: print >>sys.stderr, "SP DK240: " + \
                "Received [", list(bytearray(answer)), "]"

        return answer

    # ------------------------------------------------------------------

    def status_message(self, status, command):
        if not(status & 0x80):
            return ""

        message = "%s command failed: " % command

        if status & 0x40:
            message += "Specifier value equal to present value. "
        else:
            # Specifier value not equal to present value. 
            if status & 0x20:
                message += "Specifier was too large. "
            else:
                message += "Specifier was too small. "

        return message

    # ------------------------------------------------------------------

    def echotest(self):
        """
        Used to verify communications with the monochromator.
        Should return True if the communication has been established,
        and False otherwise.
        """
        self.reopen_if_needed()
        self.purge()
        
        self.write(chr(27))

        answer = self.read(1) # Should return 27

        if not(answer):
            return False
        
        if answer != chr(27):
            return False

        return True

    # ------------------------------------------------------------------

    def get_wavelength(self):
        """
        Return the current wavelength (in nanometers).
        """
        
        self.reopen_if_needed()
        self.purge()
        
        self.write(chr(29))

        answer = self.read(1) # Should return 29

        if not(answer):
            raise IOError("WAVE? command failed (no echo of byte 29).")
        
        if answer != chr(29):
            raise IOError("WAVE? command failed (echo different from 29).")

        # Then read the answer: wavelength (3-byte) + status (1-byte)

        answer = self.read(4) # Should return 3 bytes + status byte

        if not(answer):
            raise IOError("WAVE? command failed (no answer).")

        if len(answer) < 4:
            raise IOError("WAVE? command failed (incomplete answer).")

        bytes = bytearray(answer)
        wavelength = bytes3int(bytes[0], bytes[1], bytes[2]) / 100.0
        status = bytes[3]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "WAVE?")
            raise ValueError(message)

        return wavelength

    # ------------------------------------------------------------------

    def set_wavelength(self, wavelength):
        """
        Move the grating to the specified wavelength (in nanometers).
        """

        if wavelength > 1500.0:
            raise ValueError("SP DK240: Wavelength should be < 1500.0 nm")

        # convert into hundredth of nm encoded on 3 bytes
        bytes = int3bytes(wavelength * 100.) 

        self.reopen_if_needed()
        self.purge()
        
        self.write(chr(16))

        answer = self.read(1) # Should return 16

        if not(answer):
            raise IOError("SP DK240: " +
                          "GOTO command failed (no echo of byte 16).")
        
        if answer == chr(24):
            # Already at that wavelength position
            return

        if answer != chr(16):
            raise IOError("SP DK240: " +
                          "GOTO? command failed (echo different from 16).")

        # Then send 3-byte wavelength value (in hundredths of nanometer)

        request = str(bytearray(bytes))
        if self.debug: 
            print >>sys.stderr, ( "SP DK240: " +
                                  "Sending wavelength (3-byte value):" ), bytes
        self.write(request)

        answer = self.read(2, self.set_wavelength_timeout)

        if not(answer):
            raise IOError("SP DK240: " +
                          "GOTO command failed (no final answer).")
        
        if len(answer) < 2:
            raise IOError("SP DK240: " +
                          "GOTO command failed (incomplete final answer).")

        bytes = bytearray(answer)

        if bytes[1] != 24:
            raise IOError("SP DK240: " +
                          "GOTO command failed (missing final byte 24).")
            
        status = bytes[0]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "WAVE?")
            raise ValueError(message)

    # ------------------------------------------------------------------

    wavelength = property(get_wavelength, 
                          set_wavelength,
                          doc="Current monochromator wavelength (nanometer)")

    # ------------------------------------------------------------------


    def get_slits(self):
        """
        Return the current entrance and exit slits width (in micron).
        """
        
        self.reopen_if_needed()
        self.purge()
        
        self.serial_port.write(chr(30))

        answer = self.serial_port.read(1) # Should return 30

        if not(answer):
            raise IOError("SP DK240: " +
                          "SLIT? command failed (no echo of byte 30).")
        
        if answer != chr(30):
            raise IOError("SP DK240: " +
                          "SLIT? command failed (echo different from 30).")

        # Then read the answer: 
        # entrance (2-byte) + exit (2-byte) + status (1-byte) + byte 24

        answer = self.read(6) # Should return 4 bytes + status byte + byte 24

        if not(answer):
            raise IOError("SP DK240: " +
                          "SLIT? command failed (no answer).")

        if len(answer) < 6:
            raise IOError("SP DK240: " +
                          "SLIT? command failed (incomplete answer).")
 
        bytes = bytearray(answer)
        entrance_slit = bytes2int(bytes[0], bytes[1])
        exit_slit = bytes2int(bytes[2], bytes[3])
        status = bytes[4]
        
        if bytes[5] !=24:
            raise IOError("SP DK240: " +
                          "SLIT? command failed (missing final byte 24).")

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "SLIT?")
            raise ValueError(message)

        return entrance_slit, exit_slit, status

# -----------------------------------------------------------------

    def set_slits(self, width):
        """
        Adjust the widthness of both entrance and exit slits (in micron).
        Max value 3000 micron
        Min value 10 micron
        """
        # check the input value
        if width < 10. or width > 3000.:
            raise ValueError("SP DK240: " +
                             "The value is out range! --> [10-3000]")

        # convert into micron encoded on 2 bytes
        bytes = int2bytes(width) 
        
        self.reopen_if_needed()
        self.purge()
        
        self.serial_port.write(chr(14))
    
        answer = self.serial_port.read(1) # Should return 14

        if not(answer):
            raise IOError("SP DK240: " +
                          "SLTADJ command failed (no echo of byte 14).")
        
        if answer == chr(24):
            # Already at that position
            return

        if answer != chr(14):
            raise IOError("SP DK240: " +
                          "SLTADJ command failed (echo different from 14).")

        # Then send 2-byte width value (in millimeters)

        request = str(bytearray(bytes))
        if self.debug: 
            print >>sys.stderr, ("SP DK240: " +
                                 "Sending widthness of slits (2-byte value):", 
                                 bytes)
        self.write(request)

        # Now reading answer (HERE MAY BE WAIT MORE... -> ACTION timeout)

        # Operation time 38.5s from 10 to 3000 micron
        answer = self.read(2, self.both_slits_adjust_timeout)

        if not(answer):
            raise IOError("SP DK240: " +
                          "SLTADJ command failed (no final answer).")
        
        if len(answer) < 2:
            raise IOError("SP DK240: " +
                          "SLTADJ command failed (incomplete final answer).")

        bytes = bytearray(answer)

        if bytes[1] != 24:
            raise IOError("SP DK240: " +
                          "SLTADJ command failed (missing final byte 24).")
            
        status = bytes[0]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "SLTADJ?")
            raise ValueError(message)


 # ------------------------------------------------------------------

    def set_entrance_slit(self, width):
        """
        Adjust the widthness of the entrance slit (in micron).
        Max value 3000 micron
        Min value 10 micron
        """
        # check the input value
        if width < 10. or width > 3000.:
            raise ValueError("SP DK240: " +
                             "The slit width is out range! --> [10-3000]")

        # convert into micron encoded on 2 bytes
        bytes = int2bytes(width) 
        
        self.reopen_if_needed()
        self.purge()

        self.write(chr(31))
    
        answer = self.read(1) # Should return 31

        if not(answer):
            raise IOError("SP DK240: " + 
                          "S1ADJ command failed (no echo of byte 31).")
        
        if answer == chr(24):
            # Already at that position
            return

        if answer != chr(31):
            raise IOError("SP DK240: " + 
                          "S1ADJ command failed (echo different from 31).")

        # Then send 2-byte width value (in micron)

        request = str(bytearray(bytes))
        if self.debug: 
            print >>sys.stderr, \
                ("SP DK240: " +
                 "Sending widthness of entrance slit (2-byte value):"), bytes
        self.write(request)

        # Operation time 12.8
        answer = self.read(2, self.one_slit_adjust_timeout) 

        if not(answer):
            raise IOError("SP DK240: " + 
                          "S1ADJ command failed (no final answer).")
        
        if len(answer) < 2:
            raise IOError("SP DK240: " + 
                          "S1ADJ command failed (incomplete final answer).")

        bytes = bytearray(answer)

        if bytes[1] != 24:
            raise IOError("SP DK240: " + 
                          "S1ADJ command failed (missing final byte 24).")
            
        status = bytes[0]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "S1ADJ?")
            raise ValueError(message)

# ------------------------------------------------------------------


    def set_exit_slit(self, width):
        """
        Adjust the widthness of the exit slit (in micron).
        Max value 3000 micron
        Min value 10 micron
        """
        # check the input value
        if width < 10. or width > 3000.:
            raise IOError("SP DK240: " + 
                          "The value is out range! --> [10-3000]")

        # convert into micron encoded on 2 bytes
        bytes = int2bytes(width) 
        
        self.reopen_if_needed()
        self.purge()
        
        self.write(chr(32))
    
        answer = self.serial_port.read(1) # Should return 32

        if not(answer):
            raise IOError("SP DK240: " + 
                          "S2ADJ command failed (no echo of byte 32).")
        
        if answer == chr(24):
            # Already at that position
            return

        if answer != chr(32):
            raise IOError("SP DK240: " + 
                          "S2ADJ command failed (echo different from 32).")

        # Then send 2-byte width value (in micron)

        request = str(bytearray(bytes))
        if self.debug: 
            print >>sys.stderr, \
                ("SP DK240: " + 
                 "Sending widthness of entrance slit (2-byte value):"), bytes
        self.write(request)

        answer = self.read(2, self.one_slit_adjust_timeout)

        if not(answer):
            raise IOError("SP DK240: " + 
                          "S2ADJ command failed (no final answer).")
        
        if len(answer) < 2:
            raise IOError("SP DK240: " + 
                          "S2ADJ command failed (incomplete final answer).")

        bytes = bytearray(answer)

        if bytes[1] != 24:
            raise IOError("SP DK240: " + 
                          "S2ADJ command failed (missing final byte 24).")
            
        status = bytes[0]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "S2ADJ?")
            raise ValueError(message)

# ------------------------------------------------------------------

    def get_grating(self):
        """
        Return the current grating identifier.
        """
        
        self.reopen_if_needed()
        self.purge()
        
        self.serial_port.write(chr(19))

        answer = self.read(1) # Should return 19

        if not(answer):
            raise IOError("SP DK240: " + 
                          "GRTID? command failed (no echo of byte 19).")
        
        if answer != chr(19):
            raise IOError("SP DK240: " + 
                          "GRTID? command failed (echo different from 19).")

        # Should return 6 bytes + status byte + byte 24
        # byte #0 -> number of installed gratings
        # byte #1 -> # of currently used grating
        # byte #2-#3 -> high-low current grating ruling (rule / mm)
        # byte #4-#5 -> high-low current grating blaze wavelength (nm)

        answer = self.serial_port.read(8) 

        if not(answer):
            raise IOError("SP DK240: " + 
                          "GRTID? command failed (no answer).")

        if len(answer) < 8:
            raise IOError("SP DK240: " + 
                          "GRTID? command failed (incomplete answer).")
 
        bytes = bytearray(answer)

        gratings_number = bytes[0]
        grating = bytes[1]
        grating_ruling = bytes2int(bytes[2], bytes[3])
        grating_blaze  = bytes2int(bytes[4], bytes[5])
        status = bytes[6]
        
        if bytes[7] !=24:
            raise IOError("SP DK240: " + 
                          "GRTID? command failed (missing final byte 24).")

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "GRTID?")
            raise ValueError(message)

        return gratings_number, grating, grating_ruling, grating_blaze

# ------------------------------------------------------------------

    def set_grating(self, grating):
        """
        The command changes the current grating.
        """
        # check the input value
        if not(grating in [1,2,3]):
            raise ValueError("SP DK240: " + 
                             "The selected grating is out range! --> [1-2-3]")

        self.reopen_if_needed()
        self.purge()

        self.write(chr(26))
    
        answer = self.serial_port.read(1) # Should return 26

        if not(answer):
            raise IOError("SP DK240: " + 
                          "GRTSEL command failed (no echo of byte 26).")
        
        if answer == chr(24):
            # Already at that position
            return

        if answer != chr(26):
            raise IOError("SP DK240: " + 
                          "GRTSEL command failed (echo different from 26).")

        # Then send 1-byte value

        request = str(bytearray([grating]))
        if self.debug: 
            print >>sys.stderr, "SP DK240: Sending selected grating (1-byte value):", list(bytearray([grating]))
        self.write(request)

        answer = self.read(2, self.set_grating_timeout)  
        # Operation time

        if not(answer):
            raise IOError("SP DK240: " + 
                          "GRTSEL command failed (no final answer).")
        
        if len(answer) < 2:
            raise IOError("SP DK240: " + 
                          "GRTSEL command failed (incomplete final answer).")

        bytes = bytearray(answer)

        if bytes[1] != 24:
            raise IOError("SP DK240: " + 
                          "GRTSEL command failed (missing final byte 24).")
            
        status = bytes[0]

        # Then status byte analysis and raise exception if needed
        
        if status & 0x80:
            message = self.status_message(status, "GRTSEL")
            raise ValueError(message)


## ------------------------------------------------------------------
#     def csr(self, passband):
#         """
#         This command sets monochromator to Constant Spectral Resolution
#         mode. The slit width will vary throughout a scan. This is useful,
#         for instance, where measurement of a constant interval of frequency
#         is desired (spectral power distribution measurements).
#         The band pass value 'passband' is given in hundredth's of nanometers)
#         """
#         # ici insérer un test sur les valeurs permises...
#         # raise ValueError if needed

#         high, low = short2bytes(passband)
        
#         if not(serial_port.isOpen()): # reopen if port closed
#             self.open()

#         serial_port.flushOutput()
        
#         serial_port.write(chr(28) + '\r\n')
#         answer = serial_port.readlines() # Return 28
#         # if answer[0] != chr(28):
#         #     raise

#         # TODO: analysing answer
#         # And raise specific exception if needed (according to status)
## ------------------------------------------------------------------



# # ======================================================================
