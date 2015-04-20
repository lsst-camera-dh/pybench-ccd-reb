
import types
import lsst.testbench
import time

import xmlrpclib

B = lsst.testbench.Bench()

B.register("laser")
B.register("ttl")

# TODO: improve for the Keithleys -> register

B.DKD = xmlrpclib.ServerProxy("http://lpnlsstbench:8087/")

B.DKD.connect()

# Photodiode on the integral sphere

B.PhD = xmlrpclib.ServerProxy("http://lpnlsstbench:8900/")

B.PhD.connect()

# # First turn off all the channels, in case
# B.laser.disable()
# for ch in B.laser.allchannels:
#     B.laser.unselect(ch)

# for ch in B.laser.allchannels:
#     print "Enable Laser channel ", ch
#     B.laser.select(ch)
#     B.laser.enable()
#     time.sleep(2)
#     #
#     for n in xrange(50):
#         print B.PhD.getCurrent(), B.DKD.getCurrent()
#     #
#     print "Disable Laser channel ", ch
#     B.laser.unselect(ch)
#     B.laser.disable()
#     time.sleep(2)

def flux_ramp(self):
    import time        # requested (why ???) TO FIX
    import numpy as np # requested (why ???) TO FIX

    ramps = { 
        1: { 'Imin': 15.0, 'Imax': 35.20, 'Istep': 1. },
        2: { 'Imin': 40.0, 'Imax': 64.20, 'Istep': 1. },
        3: { 'Imin': 20.0, 'Imax': 66.00, 'Istep': 1. },
        4: { 'Imin': 30.0, 'Imax': 56.80, 'Istep': 1. }
        }

    # Turn Off Keithley continuous readout if activated
    self.PhD.readContinuous(-1)
    self.DKD.readContinuous(-1)

    # First turn off all the channels, in case
    self.laser.disable()
    for ch in self.laser.allchannels:
        self.laser.unselect(ch)
    time.sleep(2)

    self.PhD.setRate(5.)
    # self.PhD.readContinuous(1)

    self.DKD.setRate(5.)
    # self.DKD.readContinuous(1)

    print "Opening the shutter"
    self.ttl.openShutter()
    time.sleep(2)

    for ch in self.laser.allchannels:
        print "Enable Laser channel ", ch
        self.laser.select(ch)
        self.laser.enable()
        time.sleep(2)
        #
        # for n in xrange(50):
        #      print self.PhD.getCurrent(), self.DKD.getCurrent()

        print "Ramping up the current for channel ", ch
        for I in np.arange(ramps[ch]['Imin'],
                           ramps[ch]['Imax'] + ramps[ch]['Istep'],
                           ramps[ch]['Istep']):
            print "set laser current to I = ", I
            self.laser.setCurrent(ch, I)
            time.sleep(1)

            print self.laser.getCurrent(ch)
            print self.laser.getPower(ch)

            for i in xrange(1):
                # read-out
                self.PhD.startSequence(32)
                self.DKD.startSequence(32)
                while (self.DKD.status() != 0) or (self.PhD.status() != 0):
                    time.sleep(1)
                print self.PhD.getSequence()
                print self.DKD.getSequence()

        #
        print "Disable Laser channel ", ch
        self.laser.unselect(ch)
        self.laser.disable()
        time.sleep(2)


    self.ttl.closeShutter()
    time.sleep(2)

B.flux_ramp = types.MethodType(flux_ramp, B)
# Bench.flux_ramp = flux_ramp


