
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

        Instrument configuration will be taken from the default
        configuration file (config.py) if any. All parameters may be
        overridden.
        """

        if self.registry.has_key(identifier):
            print "Instrument", identifier, "is already registered"
            return


        params = {}

        if config.has_key(identifier):
            # take the parameters from there
            params.update(**config[identifier])

        # Now, overwrite parameters with the caller ones
        params.update(**kargs)

        # Create an instance of the instrument

        instrument_module   = getattr('drivers', params['driver'])
        instrument_class    = getattr(instrument_module, 'Instrument')
        instrument_instance = instrument_class(identifier, **params)
        
        # eval('import %s' % instrument_module)

        self.registry[identifier] = dict(params)

        self.__dict__[identifier] = self.registry[identifier]

        self.__dict__[identifier].register()





