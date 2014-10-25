
from singleton import Borg

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

    def register(self, identifier, instrument):
        if self.registry.has_key(identifier):
            print "Instrument", identifier, "is already registered"
            return
        self.registry[identifier] = "OK"

        self.__dict__[identifier] = "toto"


