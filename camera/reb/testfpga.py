
from fpga import *

import numpy as np
import pylab as pb

import os

# Add a graphical plotting feature

def Function_plot(self, channels = None):
    if channels == None:
        cs = range(13)
    else:
        cs = channels

    times = []
    values = {}
    for c in cs:
        values[c] = []

    t = 0.0
    slices = self.timelengths.keys()
    slices.sort()
    for sl in slices:
        if self.timelengths[sl] == 0:
            break

        times.append(t)
        t += self.timelengths[sl]
        times.append(t)

        for c in cs:
            values[c].append(self.is_on(c, sl) + 2.0 * c)
            values[c].append(self.is_on(c, sl) + 2.0 * c)

    pb.cla()
    # pb.ylim(-2, 24+2)
    for c in cs:
        pb.plot(times, values[c], "-")

    pb.yticks( pb.arange(0,25,2), 
               ('RU','RD','RS','CL', 
                'R1','R2','R3','RG',
                'P1','P2','P3','P4',
                'ST') )

    pb.savefig("functions.png")
    os.system("display functions.png")

Function.plot = Function_plot



fp = FPGA(2)

