# Sample of commands for running a CCD on the test bench with a LSST REB

from lsst.testbench.bench import Bench
B = Bench()
import lsst.testbench.scripts.ccd.functions

# for REB1: BEFORE connecting to CCD
# for REB3/4 : anytime the REB is powered on
B.initialize_REB()
# for REB1: AFTER connecting to CCD
# for REB3/4 : anytime after the REB has been initialized
B.powerup_CCD()


B.reb.set_testtype('TEST')
#B.reb.stop_waiting_sequence()
m = B.execute_reb_sequence('Acquisition', 2)
# to execute again the same sequence :
m = B.execute_reb_sequence()

# to create FITS HDU object
i = B.conv_to_fits()
#to have only channels 4 and 5:
i = B.conv_to_fits([4,5])

# to save FITS HDU with headers
B.save_to_fits(i, m) 

# to display straight from the HDU
B.register('ds9')
B.ds9.load_hdulist(i)
# see also:
# import lsst.testbench.scripts.ccd.display

# quick statistics on frame
import lsst.testbench.scripts.ccd.analysis as analysis
analysis.area_stats(i)

# between exposures 
B.reb.start_waiting_sequence()
# before beginning exposures again (now included in execute_reb_sequence())
B.reb.stop_waiting_sequence()

# scan mode
B.reb.set_testtype('SCAN')
B.reb.start_adc_increment()
m = B.execute_reb_sequence('Acquisition', 2)
i = B.conv_to_fits(borders=True)
B.save_to_fits(i, m) 
# to put ASPIC in Transparent Mode and see the raw waveform
B.reb.set_parameter('TM', 1)
# to remove Transparent Mode
B.reb.set_parameter('TM', 0)
B.reb.stop_adc_increment()

# when finished
B.shutdown_CCD()

# auxiliary instruments
B.register('laser')
B.laser.select(2)
B.laser.setCurrent(2,45.0)
B.laser.enable()
B.laser.disable()

B.register("PhD")
B.PhD.setup_current_measurements(2e-6)
B.PhD.read_measurement()

B.register('lakeshore1')

# New timing file
B.load_sequencer('sequencer-shortRC.txt')
B.reb.set_parameter('RC', 15)
B.reb.set_window(False)  # to read the full frame again (window by default)
# Computes timing
B.reb.reb.seq.timing('Bias')

# to recover REB object after Python reboot without reloading the whole sequencer
from lsst.testbench.bench import Bench
B = Bench()
import lsst.testbench.scripts.ccd.functions
#from lsst.camera.generic import rebxml
#B.reb.reb.seq = rebxml.fromxmlfile('/home/lsst/git/py/camera/reb1/sequencer-soi.xml')
# obsolete with B.reb.reb.seq now loaded in REB.__init__()
# TODO: need to recover pointers
B.reb.reb.exptime = B.reb.reb.get_exposure_time()


