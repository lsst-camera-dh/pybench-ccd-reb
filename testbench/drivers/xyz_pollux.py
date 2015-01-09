#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the XYZ Pollux motors
"""

# XML-RPC interface:
#
# # General Control Functions 
# server.register_function(XYZ.status,       "status")
# server.register_function(XYZ.open,         "open")
# server.register_function(XYZ.close,        "close")
# server.register_function(XYZ.close,        "checkConnection")

# # XYZ motion
# server.register_function(XYZ.home,         "home")
# server.register_function(XYZ.get_position, "get_position")
# # server.register_function(XYZ.position,     "position")
# server.register_function(XYZ.move,         "move")
# server.register_function(XYZ.park,         "park")

# # misc 
# server.register_function(server_quit,      "quit")

# # for remote introspection (tab completion with ipython)
# server.register_function(XYZ._listMethods,  "__dir__")
# server.register_function(XYZ._listMethods,  "system.listMethods")
# server.register_function(XYZ._listMethods,  "trait_names")
# server.register_function(XYZ._listMethods,  "_getAttributeNames")
# # TODO: implement: system.methodSignature
# server.register_function(XYZ._methodHelp,   "system.methodHelp")



from driver import Driver

import xmlrpclib

# =======================================================================

class Instrument(Driver):

    # ===================================================================
    #  Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)
        
        # self.identifier = identifier
        # self.host = host
        # self.devices = devices
        # self.port = port # XML-RPC port

        if 'host' not in kargs.keys():
            raise ValueError("host is requested")

        if 'devices' not in kargs.keys():
            raise ValueError("devices is requested")

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

        if answer == "":
            return False

        if 'XYZ' not in answer:
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        (kept to stay compatible with Edo code)
        """
        return self.xmlrpc.checkConnection()


    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("XYZ mount is not connected.")

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


    def home(self):
        """
        Home the three motors, move up and down each of the 3 motors,
        to test the mechanical motor stops and reset the motor zeros.  
        Then the mounting is parked.
        Should be called once at the begining of a run to detect
        the physical limits.
        
        WARNING: blocking call. Takes about 20s.
        
        see: XYZ.home()
        """
        result = self.xmlrpc.home()
        return result


    def park(self):
        """
        Park the XYZ out of the light beam.
        This routine may be called even if the XYZ mount
        has not yet been initialized (no homing done yet).
        """ 
        result = self.xmlrpc.park()
        return result


    def get_position(self):
        """
        Return the current position on the three motors 
        (as a dictionary).
        It is then possible to do move(**get_position())
        """
        pos = self.xmlrpc.get_position()
        return pos

    position = property(get_position, doc = "XYZ current position")


    def move(self, moves, wait = True, check = True):
        """
        Move the XYZ to the given position (or offset).
        'moves' is a dictionary of the following format:
              {'x': 12.34, 'y': -23.1, 'dz' : -45.0 }
        This function can do relative (dx,dy,dz) 
        and absolute (x,y,z) movements.

        By default, check is and *MUST* be left to True.
        """

        # logging.info("XYZ.move() called.")
        result = self.XYZ.move(wait=wait,check=check, **moves)
        # logging.info("XYZ.move() done.")
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
            'MODEL'  : 'Pollux XYZ mount',
            'DRIVER' : 'xyz-server / pyBench' 
            }

        pos = self.get_position()

        for axis in ['x', 'y', 'z']:
            key = '%sPOS' % axis.upper()
            comment = ( '[mm] Current %s position of the XYZ mount in mm' 
                        % axis.upper() )
            value = pos[axis]
            keys.append(key)
            values[key] = value
            comments[key] = comment

        return keys, values, comments

    # ===================================================================
