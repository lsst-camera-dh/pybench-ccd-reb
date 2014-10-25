
from singleton import Borg

from config import config
from drivers import * # is it a good idea ?


class Bench(Borg):
    """
    Generic class to manage the LSST CCD Testbench at LPNHE.
    This object is a singleton.
    """

    def __init__(self):
        Borg.__init__(self)
        self.val = "LSST CCD Testbench"
        self.registry = {}

    def __str__(self): 
        return self.val

    def register(self, identifier, **kargs):
        """
        Load the driver for the corresponding instrument and identifier,
        if this instrument has not been already registered.

        A first call to this method will open and check the connection
        to the instrument. Subsequent calls will do nothing, except
        if 'force_reload' is set to True.
        """

        if self.registry.has_key(identifier):
            print "Instrument", identifier, "is already registered"
            return

        self.registry[identifier] = 

        self.registry[identifier] = "OK"

        self.__dict__[identifier] = "toto"


