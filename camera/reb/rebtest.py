
import sys, os, os.path
import time
import subprocess

import lsst.camera.reb as reb

reb_id = 2

R = reb.REB(reb_id = reb_id)

# loading the default sequencer program
R.load_program()

# starting the clock register
R.fpga.start_clock()

# starting the imageClient process
# subprocess.Popen("imageClient %d" % reb_id) -> path problem
subprocess.Popen("imageClient %d" % reb_id, shell=True)

# launching a clear 10 times
R.run_subroutine('clear', repeat = 10)




# taking a bias

# time.sleep(1)
# R.run_subroutine('bias')

# taking a frame

# time.sleep(15)
# R.run_subroutine('acq')


