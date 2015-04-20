
import importlib
import logging ## critical: common logging system (all devices should log through it)
 
from singleton import Borg

from config import config

import drivers

# find a better way, to dynamically load the modules associated (from config.py)
# import drivers.laser_thorlabs  
# import drivers.xyz_pollux
# import drivers.dummy_dummy


class Bench(Borg):
    """
    Generic class to manage the LSST CCD Testbench at LPNHE.  
    This object *MUST* be a singleton.
    """

    def __init__(self):
        Borg.__init__(self)
        # Be careful here: do not reset any existing member
        if not(self.__dict__.has_key("name")):
            self.name = "LSST CCD Testbench"
        if not(self.__dict__.has_key("registry")):
            self.registry = {}

    def __str__(self): 
        return self.name

    def register(self, identifier, **kargs):
        """
        Load the driver for the corresponding instrument and
        identifier, if this instrument has not been already
        registered.

        A first call to this method will open and check the connection
        to the instrument. Subsequent calls will do nothing, except if
        'force_reload' is set to True.

        Instrument configuration will be taken from the default
        configuration file (config.py) if any. All parameters may be
        overridden.
        """

        # if this instrument (under the same identifier) is already
        # registered as a bench element, and there is no force_reload=True
        # option, do not reload the driver.
        #
        if (self.registry.has_key(identifier) and
            not(kargs.get('force_reload', False))):
            print "Instrument", identifier, "is already registered"
            return
        
        params = {}
        
        if config.has_key(identifier):
            # take the parameters from there
            params.update(**config[identifier])

        # Now, overwrite parameters with the caller ones
        params.update(**kargs)

        # Dynamically load the module
        # eval('import %s' % instrument_module)
        
        code = compile("import drivers.%s" % params['driver'], 
                       filename = '/dev/stderr',
                       mode = 'exec')
        eval(code)
        
        # Create an instance of the instrument

        instrument_module   = getattr(drivers, params['driver'])
        print instrument_module

        instrument_class    = getattr(instrument_module, 'Instrument')
        print instrument_class

        instrument_instance = instrument_class(identifier, **params)
        print instrument_instance
        print dir(instrument_instance)

        
        # register actions: try to open and connect to the instrument
        # will raise an exception if it fails
        try:
            instrument_instance.register(self)
        except:
            raise IOError("Failed to connect to instrument %s. Stop." %
                          identifier)

        # If (and only if) register() call is successful
        # Add the instrument to the registry.

        self.registry[identifier] = dict(params)
        self.registry[identifier]['instance'] = instrument_instance
        self.__dict__[identifier] = instrument_instance

        return True


    def load(self, script, **kargs):
        """
        Load the provided script. This may register new instruments,
        and graft new methods on the Bench instance (on the class in
        fact).
        """
        source = open(script).read()
        code = compile(source = source, 
                       filename = '/dev/stderr', 
                       mode = 'exec')
        eval(code)

        return True
          
    # ===================================================================
    #  Meta data / state of the instrument 
    # ===================================================================

    def get_meta(self):
        """
        Returns meta data describing the current state of all the
        registered instruments.  
        Useful to fill the FITS headers.
        """

        meta = {}
        for identifier, element in self.registry.iteritems():
            instance = element['instance']
            extname = identifier.upper()
            keys, values, comments = instance.get_meta()
            meta[identifier] = { 'extname' : extname,
                                 'keys' : keys,
                                 'values' : values,
                                 'comments' : comments }
            
        return meta

    # ===================================================================




