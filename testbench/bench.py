
from singleton import Borg

from config import config
import drivers
import drivers.laser_thorlabs


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

        instrument_module   = getattr(drivers, params['driver'])
        instrument_class    = getattr(instrument_module, 'Instrument')
        instrument_instance = instrument_class(identifier, **params)
        
        # eval('import %s' % instrument_module)

        # register actions: try to open and connect to the instrument
        # will raise an exception if it fails
        try:
            instrument_instance.register()
        except:
            raise IOError("Failed to connect to instrument %s. Stop." %
                          identifier)

        # If (and only if) register() call is successful
        # Add the instrument to the registry.

        self.registry[identifier] = dict(params)
        self.registry[identifier]['instance'] = instrument_instance
        self.__dict__[identifier] = instrument_instance






