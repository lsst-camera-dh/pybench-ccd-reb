
import sys, os, os.path
import time
import subprocess

import lsst.camera.reb as reb

reb_id = 2

R = reb.REB(reb_id = reb_id)

# Load the sequencer (program & functions) from a XML file
seq = reb.Sequencer.fromxmlfile("sequencer-soi.xml")
# print seq.program
R.send_sequencer(seq)

# starting the clock register
R.start_clock()

# Set the time to Unix time (in 10 ns = 1e-8 s unit)
R.time = int(time.time() / 10.0e-9)

# Get the time
print R.time
print time.ctime(R.time * 10.e-9)

# starting the imageClient process (requested!)
# If the CCS is running the imageClient is not needed.
# subprocess.Popen("imageClient %d" % reb_id) -> path problem
# subprocess.Popen("imageClient %d" % reb_id, shell=True)

# launching a clear 10 times
R.run_subroutine('ClearCCD', repeat = 10)

# taking a bias
time.sleep(1)
R.run_subroutine('Bias')

# taking a frame
time.sleep(15)
R.run_subroutine('Acquisition')


