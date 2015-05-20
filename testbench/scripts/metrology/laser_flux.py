import os, os.path
import types
import lsst.testbench
import time
import datetime
import numpy as np

B = lsst.testbench.Bench()

B.register("laser")
B.register("ttl")
B.register("DKD")
B.register("PhD")

print """
metrology/laser_flux_ramp
--------------------

B.laser_flux_ramp(channels = [1,2,3,4])

     Will do a flux ramp with each laser channels and measure 
     the flux obtained in the integral sphere and at the CCD position 
     with the calibrated DKD photodiode.

B.laser_stability(channel = 2, current = 45.0, repeat=10000)

     Repeat forever the same measurement to estimate the
     stability of the laser source.


"""

#------------------------------------------------------------------------

def laser_flux_ramp(self, channels = [1,2,3,4]):
    ramps = { 
        #1: { 'Imin': 15.0, 'Imax': 35.20, 'Istep': 1. },
        #2: { 'Imin': 40.0, 'Imax': 64.20, 'Istep': 1. },
        #3: { 'Imin': 20.0, 'Imax': 66.00, 'Istep': 1. },
        #4: { 'Imin': 30.0, 'Imax': 56.80, 'Istep': 1. }
        1: { 'Imin': 0.0, 'Imax': 35.20, 'Istep': 0.5 },
        2: { 'Imin': 0.0, 'Imax': 64.20, 'Istep': 0.5 },
        3: { 'Imin': 0.0, 'Imax': 66.00, 'Istep': 0.5 },
        4: { 'Imin': 0.0, 'Imax': 56.80, 'Istep': 0.5 }
        }

    # setup of the 2 Keithleys

    self.DKD.setup_current_measurements(2e-8)
    self.PhD.setup_current_measurements(2e-4)

    # First turn off all the channels, in case
    self.laser.disable()
    for ch in self.laser.allchannels:
        self.laser.unselect(ch)
    time.sleep(2)

    print "Opening the shutter"
    self.ttl.openShutter()
    time.sleep(2)

    # Create the data file
    now = datetime.datetime.utcnow()
    datadir = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            now.date().isoformat())

    if not(os.path.isdir(datadir)):
        os.makedirs(datadir)

    datafile = os.path.join(datadir,
                            ("DKD-PhD-Laser-fluxes-%s.data"
                             % now.isoformat()))
    f = open(datafile, "w")

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# time\t laser channel\t laser current\t laser power\t DKD flux\t Sphere flux"

    # for ch in self.laser.allchannels:
    for ch in channels:
        print "Enable Laser channel ", ch
        self.laser.select(ch)
        self.laser.enable()
        time.sleep(2)
        #
        print "Ramping up the current for channel ", ch
        for I in np.arange(ramps[ch]['Imin'],
                           ramps[ch]['Imax'] + ramps[ch]['Istep'],
                           ramps[ch]['Istep']):
            print "set laser current to I = ", I
            self.laser.setCurrent(ch, I)
            time.sleep(2)

            for i in xrange(20):
                now = time.time()
                lasercurrent = self.laser.getCurrent(ch)
                laserpower = self.laser.getPower(ch)
                dkdflux = self.DKD.read_measurement()
                phdflux = self.PhD.read_measurement()

                print >>f, now, ch, lasercurrent, laserpower, dkdflux, phdflux
                print now, ch, lasercurrent, laserpower, dkdflux, phdflux
        #
        print "Disable Laser channel ", ch
        self.laser.unselect(ch)
        self.laser.disable()
        time.sleep(2)

    f.close()

    self.ttl.closeShutter()
    time.sleep(2)

# B.flux_ramp = types.MethodType(flux_ramp, B)
lsst.testbench.Bench.laser_flux_ramp = laser_flux_ramp


#------------------------------------------------------------------------

def laser_stability(self, channel = 2, current = 45.0, repeat = 10000):

    # setup of the 2 Keithleys

    self.DKD.setup_current_measurements(2e-9)
    self.PhD.setup_current_measurements(2e-5)

    # First turn off all the channels, in case
    self.laser.disable()
    for ch in self.laser.allchannels:
        self.laser.unselect(ch)
    time.sleep(2)

    # Create the data file
    now = datetime.datetime.utcnow()
    datadir = os.path.join(os.getenv("HOME"),
                            "data", "metrology",
                            now.date().isoformat())

    if not(os.path.isdir(datadir)):
        os.makedirs(datadir)

    datafile = os.path.join(datadir,
                            ("DKD-PhD-Laser-flux-stability-%s.data"
                             % now.isoformat()))
    f = open(datafile, "w")

    print "Enable Laser channel ", channel
    self.laser.select(channel)
    print "set laser current to I = ", current
    self.laser.setCurrent(channel, current)
    self.laser.enable()
    time.sleep(2)

    for line in self.get_meta_text():
        print >>f, "#", line

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# time\t laser channel\t laser current\t laser power\t DKD flux\t Sphere flux\t On/Off"

    # Dark current, laser off, shutter off

    self.log("Dark current measurement")
    self.laser.disable()
    self.ttl.closeShutter()

    for i in xrange(10):
        now = time.time()
        lasercurrent = self.laser.getCurrent(channel)
        laserpower = self.laser.getPower(channel)
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, channel, lasercurrent, laserpower, dkdflux, phdflux, 0
        print now, channel, lasercurrent, laserpower, dkdflux, phdflux, 0


    self.log("Enable the laser")
    self.laser.enable()
    time.sleep(2)
    self.log("Opening the shutter")
    self.ttl.openShutter()
    time.sleep(2)
        
    for i in xrange(repeat):
        now = time.time()
        lasercurrent = self.laser.getCurrent(channel)
        laserpower = self.laser.getPower(channel)
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, channel, lasercurrent, laserpower, dkdflux, phdflux, 1
        print now, channel, lasercurrent, laserpower, dkdflux, phdflux, 1


    self.log("Dark current measurement")
    self.laser.disable()
    self.ttl.closeShutter()

    for i in xrange(10):
        now = time.time()
        lasercurrent = self.laser.getCurrent(channel)
        laserpower = self.laser.getPower(channel)
        dkdflux = self.DKD.read_measurement()
        phdflux = self.PhD.read_measurement()

        print >>f, now, channel, lasercurrent, laserpower, dkdflux, phdflux, 0
        print now, channel, lasercurrent, laserpower, dkdflux, phdflux, 0

    #
    print "Disable Laser channel ", channel
    self.laser.unselect(channel)
    self.laser.disable()
    time.sleep(2)

    f.close()

    self.ttl.closeShutter()
    time.sleep(2)

# B.laser_stability = types.MethodType(laser_stability, B)
lsst.testbench.Bench.laser_stability = laser_stability


