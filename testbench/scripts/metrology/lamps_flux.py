
import types
import lsst.testbench
import time
import datetime
import numpy as np

B = lsst.testbench.Bench()

B.register("QTH")
B.register("triax")
B.register("ttl")
B.register("DKD")
B.register("PhD")

print """
metrology/lamps_flux
--------------------

B.qth_flux(wlrange = [300.0, 1200.0], dwl = 5.0, filters = [1,2,3])

     Will do a wavelength scanning and measure the flux obtained
     in the integral sphere and at the CCD position with the 
     calibrated DKD photodiode.

"""


def qth_flux(self, wlrange = [300.0, 1200.0], dwl = 5.0, filters = [1,2,3]):
    """
    Will do a wavelength scanning and measure the flux obtained
    in the integral sphere and at the CCD position with the 
    calibrated DKD photodiode.
    """
    # Setup of the 2 Keithleys
    self.log("Setting up the 2 Keithleys...")
    self.DKD.setup_current_measurements(2e-8)
    self.PhD.setup_current_measurements(2e-4)
    self.log("Setting up the 2 Keithleys done.")

    # In case it is still open, close the safety shutter
    self.ttl.closeSafetyShutter(wait=True)


    # Turn on the QTH lamp
    self.log("Turning the QTH lamp on...")
    self.QTH.on()
    self.QTH.setFluxControl(True)
    self.log("Waiting for the lamp to be ready...")
    while self.QTH.isRamping():
        time.sleep(1)
    self.log("Waiting for the lamp to be ready done.")

    # Set up the Triax monochromator
    self.triax.setInSlit(1400,  wait=True)
    self.triax.setOutSlit(1400, wait=True)
    self.log("Waiting for the monochromator to be ready...")
    self.log("Waiting for the monochromator to be ready done.")

    # Create the data file
    now = datetime.datetime.utcnow()
    datadir = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            now.date().isoformat())

    if not(os.path.isdir(datadir)):
        os.makedirs(datadir)

    datafile = os.path.join(datadir,
                            ("DKD-PhD-QTH-triax-fluxes-%s.data"
                            % now.isoformat()))
    f = open(datafile, "w")

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# QTH lamp through monochromator"
    print >>f, "# Entrance slit = ", self.triax.getInSlit()
    print >>f, "# Exit slit = ", self.triax.getOutSlit()
    print >>f, "# time\t filter\t grating\t wavelength\t lamp current\t laamp power\t DKD flux\t Sphere flux"

    # for ch in self.laser.allchannels:
    for filt in filters:
        self.log("Changing to filter %d ..." % filt)
        # Important: first close the safety shutter
        self.ttl.closeSafetyShutter(wait=True)
        self.ttl.moveFilter(filt, wait=True)
        self.ttl.openSafetyShutter(wait=True)
        self.log("Changing to filter %d done." % filt)

        self.ttl.openShutter()

        for wl in np.arange(wlrange[0], wlrange[1] + dwl, dw):
            print "set wavelength to ", wl, "nm"
            self.triax.setWavelength(wl, wait=True)

            # for i in xrange(20):
            for i in xrange(1):
                now = time.time()
                lampcurrent = self.QTH.getCurrent()
                lamppower = self.QTH.getPower()
                eff_wl = self.triax.getWavelength()
                dkdflux = self.DKD.read_measurement()
                phdflux = self.PhD.read_measurement()

                print >>f, now, filt, grating, eff_wl, \
                    lampcurrent, lamppower, dkdflux, phdflux
                print now, filt, grating, eff_wl, \
                    lampcurrent, lamppower, dkdflux, phdflux

        self.ttl.closeShutter()

    f.close()

    # In case...
    self.ttl.closeSafetyShutter()
    self.ttl.closeShutter()

# Attach this method to the Bench class / instance
lsst.testbench.Bench.qth_flux = qth_flux



