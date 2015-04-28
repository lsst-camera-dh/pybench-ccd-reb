
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
    B.log("Setting up the 2 Keithleys...")
    self.DKD.setup_current_measurements(2e-8)
    self.PhD.setup_current_measurements(2e-4)
    B.log("Setting up the 2 Keithleys done.")

    # Turn on the QTH lamp
    B.log("Turning the QTH lamp on...")
    B.QTH.on()
    B.QTH.setFluxControl(True)
    B.log("Waiting for the lamp to be ready...")
    while B.QTH.isRamping():
        time.sleep(1)
    B.log("Waiting for the lamp to be ready done.")

    # Set up the Triax monochromator
    B.triax.setInSlit(1400,  wait=True)
    B.triax.setOutSlit(1400, wait=True)
    B.log("Waiting for the monochromator to be ready...")
    B.log("Waiting for the monochromator to be ready done.")
    
    now = datetime.datetime.utcnow()
    datafile = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            "DKD-PhD-QTH-triax-fluxes-%s.data" 
                            % now.isoformat()))
    f = open(datafile, "w")

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# QTH lamp through monochromator"
    print >>f, "# Entrance slit = ", B.triax.getInSlit()
    print >>f, "# Exit slit = ", B.triax.getOutSlit()
    print >>f, "# time\t filter\t grating\t wavelength\t lamp current\t laamp power\t DKD flux\t Sphere flux"

    # for ch in self.laser.allchannels:
    for filt in filters:
        B.log("Changing to filter %d ..." % filt)
        # Important: first close the safety shutter
        self.ttl.closeSafetyShutter(wait=True)
        self.ttl.moveFilter(filt, wait=True)
        self.ttl.openSafetyShutter(wait=True)
        B.log("Changing to filter %d done." % filt)

        B.ttl.openMellesShutter()

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

        B.ttl.closeMellesShutter()

    f.close()


    self.ttl.closeSafetyShutter()

    self.ttl.closeMellesShutter()
    # time.sleep(2)

lsst.testbench.Bench.qth_flux = qth_flux



