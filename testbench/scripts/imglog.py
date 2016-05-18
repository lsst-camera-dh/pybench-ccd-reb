from lsst.testbench.bench import Bench
B = Bench()
import lsst.testbench.scripts.ccd.functions

# for REB1: BEFORE connecting to CCD
# for REB3 : anytime the REB is powered on
B.initialize_REB()
# for REB1: AFTER connecting to CCD
B.powerup_CCD()
B.reb.set_testtype('TEST')
m = B.execute_reb_sequence('Acquisition', 2)
# to execute again the same sequence :
m = B.execute_reb_sequence()

# to create FITS HDU object
i = B.conv_to_fits()
#to have only channels 4 and 5:
i = B.conv_to_fits([4,5])

# to save FITS HDU with headers
B.save_to_fits(i, m) 

# between exposures TO BE TESTED
B.reb.start_waiting_sequence()
B.reb.stop_waiting_sequence(p)

# when finished
B.shutdown_CCD()

B.register('laser')
B.laser.select(2)
B.laser.setCurrent(2,45.0)
B.laser.enable()
B.laser.disable()


B.register("PhD")
B.PhD.setup_current_measurements(2e-6)
B.PhD.read_measurement()

B.register('lakeshore1')


# to recover REB object after Python reboot without reloading the whole sequencer
from lsst.testbench.bench import Bench
B = Bench()
import lsst.testbench.scripts.ccd.functions
#from lsst.camera.generic import rebxml
#B.reb.reb.seq = rebxml.fromxmlfile('/home/lsst/git/py/camera/reb1/sequencer-soi.xml')
# obsolete with B.reb.reb.seq now loaded in REB.__init__()
# TODO: need to recover pointers
B.reb.reb.exptime = B.reb.reb.get_exposure_time()


