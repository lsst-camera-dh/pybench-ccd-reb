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
# =======================================================================

class Instrument(Driver):

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

        if answer == 0x80:
            return True

        return False

        
    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.read(0x01) # should be 0x80


    def register(self, bench):
        self.open()
        time.sleep(1)
        connected = self.is_connected()
        if not(connected):
            raise IOError("DICE CLAP not connected.")

        Driver.register(self, bench)


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
               channels = [1],
               period = 1600, # in 20ns ticks
               wordcount = 32000,  
               blocksize = 32768):
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

        return self.xmlrpc.sample(channels = channels,
                                  period = period, # in 20ns ticks
                                  wordcount = wordcount,  
                                  blocksize = blocksize)
        


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
            data = np.array(struct.unpack(fmt, a['data'].data))
            result['data'] = data

        return result

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

        keys.append('CHANNELS')
        values['CHANNELS'] = str(dataset['channels'])
        comments['CHANNELS'] = "CLAP channels"
        
        key.append('PERIOD')
        values['PERIOD'] = dataset['period']
        comments['PERIOD'] = "[x 20ns] CLAP sampling period"
        
        key.append('BLOCKSZ')
        values['BLOCKSZ'] = dataset['blocksize']
        comments['BLOCKSZ'] = "CLAP transfer block size"

        key.append('TIMESTMP')
        values['TIMESTMP'] = dataset['timestamp']
        comments['TIMESTMP'] = "Unix timestamp of the PC"

        key.append('CLAPTIME')
        values['CLAPTIME'] = dataset['board_timestamp']
        comments['CLAPTIME'] = "[x 20 ns] CLAP internal clock"
        
        return keys, values, comments, dataset.get('data', [])

    # ===================================================================


