
import os
import lsst.testbench
import time
import numpy as np

B = lsst.testbench.Bench()

B.register("QTH")
B.register("triax")
B.register("ttl")
B.register('lakeshore1')
#B.register("DKD")
# done in ccd.functions:
#B.register("PhD")
#B.register('reb')  # connect to the REB
#B.register('bss')  # connect (remotely) to the BackSubstrate Power

import lsst.testbench.scripts.ccd.functions

print """
CCD metrology with QTH lamp
--------------------

B.qth_flux(exptimes = [0.5, 2],
           wlrange = [300.0, 1200.0], dwl = 5.0,
           grating = 1, filt = 1,
           )

     Will do a wavelength scanning and measure the flux obtained
     in the integral sphere and take a pair of flats with the given
     exposure times (plus a bias).

CCD must be powered up BEFORE running the script

"""

validamps = [2, 3, 4, 5, 6, 11, 12, 13, 14, 15]
serno = '100-00'
eodir = os.path.join('/data/eotest/', serno, 'qe/scan_ccd_QE-v0/', time.strftime('%Y%m%d'))
if not os.path.isdir(eodir):
    os.makedirs(eodir)

# CCD must be powered up before running the script

# ==============================================================================

def qth_flux(self,
             exptimes = [0.5, 2],
             wlrange = [300.0, 1200.0], dwl = 5.0, 
             grating = 1, filt = 1,
             ):
    """
    Will do a wavelength scanning and measure the flux obtained
    in the integral sphere and take a pair of flats with the given
    exposure times (plus a bias).
    """

    # In case it is still open, close the safety shutter
    self.ttl.closeSafetyShutter(wait=True)

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

    #self.powerup_CCD()
    self.reb.set_testtype('QE')

    # Setup of the 2 Keithleys
    self.log("Setting up the Keithley...")
    #self.DKD.setup_current_measurements(DKD_range)
    self.PhD.setup_current_measurements(2e-8)
    self.log("Setting up the Keithley done.")

    # Set up the Triax monochromator
    self.log("Waiting for the monochromator to be ready...")
    self.triax.setInSlit(1400,  wait=True)
    self.triax.setOutSlit(1400, wait=True)
    self.log("Waiting for the monochromator to be ready done.")

    # Create the logging summary file
    # TODO: build file structure and file names
    summaryfile = os.path.join(eodir, 'summary.log')
    f = open(summaryfile, 'a')

    print >>f, "# fluxes on the LSST CCD testbench"
    print >>f, "# QTH lamp through monochromator"
    print >>f, "# Entrance slit = ", self.triax.getInSlit()
    print >>f, "# Exit slit = ", self.triax.getOutSlit()
    print >>f, "# wavelength\t exposure time\t file name"

    self.log("Changing to filter %d ..." % filt)
    # Important: first close the safety shutter (as the wheel may go to unprotected positions)
    self.ttl.closeSafetyShutter(wait=True)
    self.ttl.moveFilter(filt)
    self.log("Changing to filter %d done." % filt)

    self.log("Changing to grating %d ..." % grating)
    self.triax.setGrating(grating, wait=True)
    time.sleep(2)
    self.log("Changing to grating %d done." % grating)

    # start wavelength scan
    for wl in np.arange(wlrange[0], wlrange[1] + dwl, dwl):
        print "set wavelength to ", wl, "nm"
        self.triax.setWavelength(wl, wait=True)
        time.sleep(2)
        eff_wl = self.triax.getWavelength()  # there seems to be a bug

        # First take bias frame
        self.log("Taking bias")
        self.ttl.closeSafetyShutter(wait=True)
        m = self.execute_reb_sequence(True, 'ClearBias', 0, 20)
        #to have only useful channels:
        fname = "%s_lambda_%04d_bias_%s.fits" % (serno, int(eff_wl), self.reb.reb.imgtag)
        i = self.conv_to_fits(channels=validamps)
        # to save FITS HDU with headers
        self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

        print >>f, eff_wl, 0, fname

        # Turn on the light
        self.ttl.openSafetyShutter()

        for t in exptimes:
            # pair of flats
            for numpair in [1, 2]:
                m = self.execute_reb_sequence(True, 'Acquisition', t)
                #to have only useful channels:
                 #fname = lab['camera'].exp_acq(fname, exptime, path=datadir,  )
                fname = "%s_lambda_%04d_qe%d_%05u_%s.fits" % (serno, int(eff_wl), numpair, int(t*100), self.reb.reb.imgtag)
                i = self.conv_to_fits(channels=validamps)
                # to save FITS HDU with headers
                self.save_to_fits(i, m, fitsname=os.path.join(eodir, fname))

                print >>f, eff_wl, t, fname

    f.close()

    # Shutting down (not the lamp by default)
    self.ttl.closeSafetyShutter()
    #self.shutdown_CCD()
    # p = self.reb.start_waiting_sequence()


# Attach this method to the Bench class / instance
lsst.testbench.Bench.qth_flux = qth_flux
