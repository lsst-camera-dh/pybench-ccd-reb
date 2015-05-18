
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
           grating = 1, filt = 1,
           DKD_range = 2.0e-9,
           PhD_range = 2.0e-8,
           n = 10)

     Will do a wavelength scanning and measure the flux obtained
     in the integral sphere and at the CCD position with the 
     calibrated DKD photodiode.

B.qth_flux_all(wlrange = [300.0, 1200.0], dwl = 5.0, 
               n = 10)

     Will do a wavelength scanning for all combinations 
     of filter and gratings.


B.qth_stability(wl = 500.0, grating = 0, filt = 1, 
                current_range = 2e-10, repeat = 10000)

     Repeat the same measurement to estimate the stability 
     of the QTH.

"""

# ==============================================================================

def qth_flux(self, 
             wlrange = [300.0, 1200.0], dwl = 5.0, 
             grating = 1, filt = 1,
             DKD_range = 2.0e-11,
             PhD_range = 2.0e-7,
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
    if not(self.QTH.isOn()):
        self.log("Error: you should turn the lamp on first.")
        return

    if not(self.QTH.isFluxControlled()):
        self.log("Error: you should turn the lamp flux control on first.")
        return

    # Setup of the 2 Keithleys
    self.log("Setting up the 2 Keithleys...")
    self.DKD.setup_current_measurements(DKD_range)
    self.PhD.setup_current_measurements(PhD_range)
    self.log("Setting up the 2 Keithleys done.")

    # In case it is still open, close the safety shutter
    self.ttl.closeSafetyShutter(wait=True)


    # Set up the Triax monochromator
    self.log("Waiting for the monochromator to be ready...")
    self.triax.setInSlit(1400,  wait=True)
    self.triax.setOutSlit(1400, wait=True)
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
    print >>f, "# time\t filter\t grating\t wavelength\t lamp current\t lamp power\t DKD flux\t Sphere flux\t On/Off"

    self.log("Changing to filter %d ..." % filt)
    # Important: first close the safety shutter (as the wheel may go to unprotected positions)
    self.ttl.closeSafetyShutter(wait=True)
    self.ttl.moveFilter(filt)
    self.log("Changing to filter %d done." % filt)

    self.log("Changing to grating %d ..." % grating)
    self.triax.setGrating(grating, wait=True)
    time.sleep(2)
    self.log("Changing to grating %d done." % grating)

    # Now write meta info in the data file
    for line in self.get_meta_text():
        print >>f, "#", line


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

    # Turn on the light

    self.ttl.openSafetyShutter()
    self.ttl.openShutter()

    for wl in np.arange(wlrange[0], wlrange[1] + dwl, dwl):
        print "set wavelength to ", wl, "nm"
        self.triax.setWavelength(wl, wait=True)
        time.sleep(2)
        eff_wl = self.triax.getWavelength() # there seems to be a bug

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

    f.close()

    # In case...
    self.ttl.closeSafetyShutter()
    self.ttl.closeShutter()

# Attach this method to the Bench class / instance
lsst.testbench.Bench.qth_flux = qth_flux


# ==============================================================================

def qth_flux_all(self,
                 wlrange = [300.0, 1200.0], dwl = 5.0, 
                 n = 10):
    
    # settings for DKD and PhD Keithleys

    DKD_range = 2e-11
    PhD_range = 2e-7 

    for filt in [1,2,3]:
        for grating in [0,1,2]:
            self.qth_flux(wlrange = wlrange, dwl = dwl,
                          grating = grating, filt = filt,
                          DKD_range = DKD_range,
                          PhD_range = PhD_range,
                          n = n)

# Attach this method to the Bench class / instance
lsst.testbench.Bench.qth_flux_all = qth_flux_all

# ==============================================================================

def qth_stability(self,
                  wl = 500.0, grating = 0, filt = 1, 
                  DKD_range = 2e-10, 
                  PhD_range = 2e-7, 
                  repeat = 10000):
    """
    Repeat the same measurement to estimate the stability 
    of the QTH.
    """

    # Check if the lamp is already on
    # and the flux control also
    if not(self.QTH.isOn()):
        self.log("Error: you should turn the lamp on first.")
        return

    if not(self.QTH.isFluxControlled()):
        self.log("Error: you should turn the lamp flux control on first.")
        return

    # setup of the 2 Keithleys

    self.DKD.setup_current_measurements(DKD_range)
    self.PhD.setup_current_measurements(PhD_range)

    # In case it is still open, close the safety shutter
    # self.ttl.closeSafetyShutter(wait=True)

    self.log("Changing to filter %d ..." % filt)
    # Important: first close the safety shutter (as the wheel may go to unprotected positions)
    self.ttl.closeSafetyShutter(wait=True)
    self.ttl.moveFilter(filt)
    self.log("Changing to filter %d done." % filt)

    # Set up the Triax monochromator
    self.log("Waiting for the monochromator to be ready...")
    self.triax.setInSlit(1400,  wait=True)
    self.triax.setOutSlit(1400, wait=True)
    self.log("Changing to grating %d ..." % grating)
    self.triax.setGrating(grating, wait=True)
    time.sleep(2)
    self.log("Changing to grating %d done." % grating)
    self.triax.setWavelength(wl, wait=True)
    self.log("Waiting for the monochromator to be ready done.")

    # Create the data file
    now = datetime.datetime.utcnow()
    datadir = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            now.date().isoformat())

    if not(os.path.isdir(datadir)):
        os.makedirs(datadir)

    datafile = os.path.join(datadir,
                            ("DKD-PhD-QTH-triax-flux-stability-%s.data"
                            % now.isoformat()))
    f = open(datafile, "w")

    print >>f, "# flux on the LSST CCD testbench"
    print >>f, "# QTH lamp through monochromator"
    print >>f, "# Stability check"
    print >>f, "# Entrance slit = ", self.triax.getInSlit()
    print >>f, "# Exit slit = ", self.triax.getOutSlit()
    print >>f, "# time\t filter\t grating\t wavelength\t lamp current\t lamp power\t DKD flux\t Sphere flux\t On/Off"

    # Now write meta info in the data file
    for line in self.get_meta_text():
        print >>f, "#", line


    # Taking data
    # dark current regularly measured by closing the Melles shutter
    # and the safety shutter


    ndark = 20
    freq = 100
    shutter_open = 1

    eff_wl = self.triax.getWavelength()

    for i in xrange(repeat + ndark):
        # interleaving dark measurements
        if (i % freq) == 0:
            shutter_open = 0
            self.ttl.closeSafetyShutter(wait=True)
            self.ttl.closeShutter(wait=True)
            time.sleep(2)
        elif (i % freq) == ndark:
            shutter_open = 1
            self.ttl.openSafetyShutter(wait=True)
            self.ttl.openShutter(wait=True)
            time.sleep(2)

        now = time.time()
        lampcurrent = self.QTH.getAmps()
        lamppower = self.QTH.getWatts()
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, filt, grating, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, shutter_open
        print now, filt, grating, eff_wl, \
            lampcurrent, lamppower, dkdflux, phdflux, shutter_open

    f.close()

    self.ttl.closeShutter()
    self.ttl.closeSafetyShutter()
    time.sleep(2)

lsst.testbench.Bench.qth_stability = qth_stability

# ==============================================================================
