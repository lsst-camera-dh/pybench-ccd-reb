
import types
import lsst.testbench
import time
import datetime
import numpy as np

B = lsst.testbench.Bench()

B.register("laser")
B.register("ttl")

lsst.testbench.config['DKD'] = dict(lsst.testbench.config['keithley'])
lsst.testbench.config['PhD'] = dict(lsst.testbench.config['keithley'])
lsst.testbench.config['PhD']['port'] = 8212

B.register("DKD")
B.register("PhD")

def setup(self, current_range):
    self.send("*RST")
    self.send("SYST:ZCH ON")
    self.send("FUNC 'CURR:DC'")
    self.send("CURR:RANG %.2g" % current_range)
    self.send("SYST:ZCOR ON")
    self.send("SYST:ZCH OFF")

B.DKD.setup = types.MethodType(setup, B.DKD)
B.PhD.setup = types.MethodType(setup, B.PhD)

def read(self):
    s = self.send("READ?")
    elts = s.split(",")
    if len(elts) < 2:
        print >>sys.stderr, "error: no data from the photodiode Keithley, stop."
        sys.exit(3)
    measure = float(elts[0].replace('A', ''))
    return measure

B.DKD.read = types.MethodType(read, B.DKD)
B.PhD.read = types.MethodType(read, B.PhD)


def flux_ramp(self):
    # import time        # requested (why ???) TO FIX
    # import datetime    # requested (why ???) TO FIX
    # import numpy as np # requested (why ???) TO FIX

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

    self.DKD.setup(2e-8)
    self.PhD.setup(2e-4)

    # First turn off all the channels, in case
    self.laser.disable()
    for ch in self.laser.allchannels:
        self.laser.unselect(ch)
    time.sleep(2)

    print "Opening the shutter"
    self.ttl.openShutter()
    time.sleep(2)

    now = datetime.datetime.utcnow()
    datafile = "DKD-PhD-Laser-fluxes-%s.data" % now.isoformat()
    f = open(datafile, "w")

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# time\t laser channel\t laser current\t laser power\t DKD flux\t Sphere flux"

    for ch in self.laser.allchannels:
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
                dkdflux = self.DKD.read()
                phdflux = self.PhD.read()

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
lsst.testbench.Bench.flux_ramp = flux_ramp


