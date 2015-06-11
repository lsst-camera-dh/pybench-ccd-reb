#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the DICE CLAP
"""

# XML-RPC interface:
#
# # General Control Functions 
# server.register_function(clap.status,       "status")
# server.register_function(clap.open,         "open")
# server.register_function(clap.close,        "close")
# server.register_function(clap.reset,        "reset")
# server.register_function(clap.clear,        "clear")

# # Clap commands
# server.register_function(clap.read,         "read")
# server.register_function(clap.read_at,      "read_at")
# server.register_function(clap.write,        "write")
# server.register_function(clap.write_at,     "write_at")
# server.register_function(clap.sample,       "sample")
# server.register_function(clap.sample,       "get_sampling_data")


from driver import Driver

import time
import xmlrpclib
import logging
import struct
import numpy as np

# =======================================================================

class Instrument(Driver):

    default_channels  = [1]
    default_period    = 1600 # in 20ns ticks
    default_wordcount = 32000
    default_blocksize = 32768

    # ===================================================================
    #  Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)
        
        # self.identifier = identifier
        # self.host = host
        # self.device = device
        # self.port = port # XML-RPC port

        if 'host' not in kargs.keys():
            raise ValueError("host is requested")

        # if 'devices' not in kargs.keys():
        #     raise ValueError("devices is requested")

        if 'port' not in kargs.keys():
            raise ValueError("port is requested")

        # sampling parameters

        if 'channels' not in kargs.keys():
            self.channels = self.default_channels 

        if 'period' not in kargs.keys():
            self.period = self.default_period

        if 'wordcount' not in kargs.keys():
            self.wordcount = self.default_wordcount

        if 'blocksize' not in kargs.keys():
            self.blocksize = self.default_blocksize

        self.xmlrpc = xmlrpclib.ServerProxy("http://%s:%d/" % 
                                            (self.host, self.port))

    def open(self):
        """
        Open the hardware connection.
        """
        self.xmlrpc.open()


    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        Returns True if the hardware answers, False otherwise.
        """
        answer = self.checkConnection()
        # print answer
        # print type(answer)

        if answer == 0x80:
            return True

        return False

        
    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.read(0x01) # should be 0x80


    def register(self, bench):
        # print "[1]"
        self.open()
        # print "[2]"
        time.sleep(1)
        # print "[3]"
        connected = self.is_connected()
        # print "[3.5]"
        if not(connected):
            # print "[3.5 ARRGHHH]"
            raise IOError("DICE CLAP not connected.")

        # print "[4]"
        Driver.register(self, bench)
        # print "[5]"


    def close(self):
        """
        Close the hardware connection.
        """
        self.xmlrpc.close()
        # TODO: Check errors


    # ===================================================================
    #  Instrument specific methods
    # ===================================================================

    def status(self):
        """
        Return the CLAP status.
        True = Ready / False = Sampling.
        """
        return self.xmlrpc.status()

    def read(self, addr):
        return self.xmlrpc.read(addr)

    def read_at(self, addr_start, addr_stop):
        return self.xmlrpc.read_at(addr_start, addr_stop)

    def write(self, addr, word):
        return self.xmlrpc.write(addr, word)

    def write_at(self, addr_start, addr_stop, value):
        return self.xmlrpc.write_at(addr_start, addr_stop, value)

    def sample(self, 
               channels  = self.channels,
               period    = self.period, # in 20ns ticks
               wordcount = self.wordcount,  
               blocksize = self.blocksize):
        """
        Request a sampling of the CLAP.
        To check if the sampling is achieved,
        call the status() method.
        """
        # ------ First checking arguments

        if wordcount > 8387583:
            logging.error(
                "wordcount too large. Should be <= 8387583 (FIFO size).")
            raise ValueError(
                "wordcount too large. Should be <= 8387583 (FIFO size).")
            
        # sampling frequency should be in [1 kHz: 500 kHz]
        #   1 kHz -> period =   100 ticks of 20 ns
        # 500 kHz -> period = 50000 ticks of 20 ns
        # 
        if not( (100 <= period) and (period <= 50000) ):
            logging.error("period should be in range [100:50000].")
            raise ValueError("period should be in range [100:50000].")

        # --

        return self.xmlrpc.sample(channels,
                                  period, # in 20ns ticks
                                  wordcount,  
                                  blocksize)


    def get_sampling_data(self):
        """
        Return the data and meta data from the last sampling
        as a dictionary.
        Return an empty dictionary if no sampling has been done yet.
        """

        result = dict(self.xmlrpc.get_sampling_data())
        
        if result.has_key('binarydata'):
            blurb = result['binarydata'].data
            fmt = "<%dh" % (len(blurb) / 2)
            data = np.array(struct.unpack(fmt, blurb))
            result['data'] = data

        return result

    # ===================================================================
    # PRE/POST exposure hooks
    # ===================================================================

    def pre_exposure(self, exptime):

        if not(self.status()):  # not ready (???)
            return

        if exptime == None:
            return

        # start a sampling
        if exptime < 2.0:
            duration = 4.0
        else:
            duration = 2.0 * exptime

        self.wordcount = duration / ( self.period * 20.0e-9)
        
        self.sample(channels = self.channels,
                    period = self.period, # in 20ns ticks
                    wordcount = self.wordcount,  
                    blocksize = self.blocksize):


    def post_exposure(self):
        # If a sampling is still running, wait until it ends
        while not(self.status()):
            time.sleep(0.5)

    # ===================================================================
    #  Meta data / state of the instrument 
    # ===================================================================

    def get_meta(self):
        """
        Returns meta data describing the current state
        of the instrument. 
        Useful to fill the FITS headers.
        """

        # keys : specify the key order
        keys = ['MODEL',
                'DRIVER']

        # comments : meaning of the keys
        comments = {
            'MODEL'  : 'Instrument model',
            'DRIVER' : 'Instrument software driver' 
            }

        values = {
            'MODEL'  : 'DICE CLAP',
            'DRIVER' : 'clap-server / sensor_clap' 
            }

        dataset = self.get_sampling_data()

        if dataset.has_key('channels'):
            keys.append('CHANNELS')
            values['CHANNELS'] = str(dataset['channels'])
            comments['CHANNELS'] = "CLAP channels"
        
        if dataset.has_key('period'):
            keys.append('PERIOD')
            values['PERIOD'] = dataset['period']
            comments['PERIOD'] = "[x 20ns] CLAP sampling period"
        
        if dataset.has_key('blocksize'):
            keys.append('BLOCKSZ')
            values['BLOCKSZ'] = dataset['blocksize']
            comments['BLOCKSZ'] = "CLAP transfer block size"

        if dataset.has_key('timestamp'):
            keys.append('TIMESTMP')
            values['TIMESTMP'] = dataset['timestamp']
            comments['TIMESTMP'] = "Unix timestamp of the PC"

        if dataset.has_key('board_timestamp'):
            keys.append('CLAPTIME')
            values['CLAPTIME'] = dataset['board_timestamp']
            comments['CLAPTIME'] = "[x 20 ns] CLAP internal clock"
        
        return keys, values, comments, dataset.get('data', [])

    # ===================================================================

