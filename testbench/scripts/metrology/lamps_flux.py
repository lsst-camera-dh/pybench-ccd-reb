
import types
import os, os.path
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

B.qth_flux(wlrange = [300.0, 1200.0], dwl = 5.0, 
           gratings=[0,1,2],
           filters = [1,2,3],
           n = 10)

     Will do a wavelength scanning and measure the flux obtained
     in the integral sphere and at the CCD position with the 
     calibrated DKD photodiode.

"""

def qth_flux(self, wlrange = [300.0, 1200.0], dwl = 5.0, 
             gratings=[0,1,2],
             filters = [1,2,3],
             n = 10):
    """
    Will do a wavelength scanning and measure the flux obtained
    in the integral sphere and at the CCD position with the 
    calibrated DKD photodiode.
    """

    # # Turn on the QTH lamp
    # self.log("Turning the QTH lamp on...")
    # self.QTH.on(wait=True)
    # self.QTH.setFluxControl(True)
    # self.log("Waiting for the lamp to be ready...")
    # self.log("Waiting for the lamp to be ready done.")
    
    # Check if the lamp is already on
    # and the flux control also
    # if not(self.QTH.isOn()):
    #     self.log("Error: you should turn the lamp on first.")
    #     return

    # if self.QTH.isFluxControlled():
    #     self.log("Error: you should turn the lamp flux control on first.")
    #     return

    # Setup of the 2 Keithleys
    self.log("Setting up the 2 Keithleys...")
    self.DKD.setup_current_measurements(2e-9)
    self.PhD.setup_current_measurements(2e-8)
    self.log("Setting up the 2 Keithleys done.")

    # In case it is still open, close the safety shutter
    self.ttl.closeSafetyShutter(wait=True)


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

    for line in self.get_meta_text():
        print >>f, "#", line
    
    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# QTH lamp through monochromator"
    print >>f, "# Entrance slit = ", self.triax.getInSlit()
    print >>f, "# Exit slit = ", self.triax.getOutSlit()
    print >>f, "# time\t filter\t grating\t wavelength\t lamp current\t lamp power\t DKD flux\t Sphere flux"

    # First take dark current

    self.log("Taking dark current measurements")
    self.ttl.closeSafetyShutter(wait=True)
    self.ttl.closeShutter(wait=True)

    for i in xrange(n):
        now = time.time()
        lampcurrent = self.QTH.getAmps()
        lamppower = self.QTH.getWatts()
        eff_wl = self.triax.getWavelength()
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, -1, -1, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, 0
        print now, -1, -1, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, 0

    # for ch in self.laser.allchannels:
    for filt in filters:
        self.log("Changing to filter %d ..." % filt)
        # Important: first close the safety shutter
        self.ttl.closeSafetyShutter(wait=True)
        self.ttl.moveFilter(filt)
        self.ttl.openSafetyShutter(wait=True)
        self.log("Changing to filter %d done." % filt)

        for grating in gratings:
            self.log("Changing to grating %d ..." % grating)
            self.triax.setGrating(grating, wait=True)
            time.sleep(2)
            self.log("Changing to grating %d done." % grating)

            self.ttl.openShutter()

            for wl in np.arange(wlrange[0], wlrange[1] + dwl, dwl):
                print "set wavelength to ", wl, "nm"
                self.triax.setWavelength(wl, wait=True)
                time.sleep(2)
                eff_wl = self.triax.getWavelength()

                for i in xrange(n):
                    now = time.time()
                    lampcurrent = self.QTH.getAmps()
                    lamppower = self.QTH.getWatts()
                    eff_wl = self.triax.getWavelength()
                    dkdflux = self.DKD.read_measurement()
                    phdflux = self.PhD.read_measurement()

                    print >>f, now, filt, grating, eff_wl, \
                        lampcurrent, lamppower, dkdflux, phdflux, 1
                    print now, filt, grating, eff_wl, \
                        lampcurrent, lamppower, dkdflux, phdflux, 1

            self.ttl.closeShutter()

    f.close()

    self.log("Taking dark current measurements")
    self.ttl.closeSafetyShutter(wait=True)
    self.ttl.closeShutter(wait=True)

    for i in xrange(n):
        now = time.time()
        lampcurrent = self.QTH.getAmps()
        lamppower = self.QTH.getWatts()
        eff_wl = self.triax.getWavelength()
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, filt, grating, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, 0
        print now, filt, grating, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, 0

    # In case...
    self.ttl.closeSafetyShutter()
    self.ttl.closeShutter()

# Attach this method to the Bench class / instance
lsst.testbench.Bench.qth_flux = qth_flux



