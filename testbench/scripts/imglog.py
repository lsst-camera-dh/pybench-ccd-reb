import lsst.testbench.bench as bench
B = bench.Bench()
import lsst.testbench.scripts.ccd.functions

# BEFORE connecting to CCD
B.initialize_REB()
# AFTER connecting to CCD
B.powerup_CCD()
m = B.execute_reb_sequence(True, 'Acquisition', 2)
# to execute again the same sequence :
m = B.execute_reb_sequence()

# to create FITS HDU object
i = B.conv_to_fits()
#to have only channels 4 and 5:
i = B.conv_to_fits([4,5])

# to save FITS HDU with headers
B.save_to_fits(i, m) 

# when finished
B.shutdown_CCD()

B.register('laser')
B.laser.select(2)
B.laser.enable()
B.laser.disable()


B.register("PhD")
B.PhD.setup_current_measurements(2e-6)
B.PhD.read_measurement()


# to recover REB object after Python reboot without reloading the whole sequencer
import lsst.testbench.bench as bench
B = bench.Bench()
import lsst.testbench.scripts.ccd.functions
from lsst.camera.generic import rebxml
B.reb.reb.seq = rebxml.fromxmlfile('/home/lsst/git/py/camera/reb1/sequencer-soi.xml')
B.reb.reb.exptime = B.reb.reb.get_exposure_time()


