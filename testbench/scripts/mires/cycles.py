# ! /usr/bin/env python
# -*- Coding: utf-8 -*-
#
# LSST
#
# Projection d'une mire sur le CCD
# 

import os
import time
import logging

import lsst.testbench.bench as bench

B = bench.Bench()  # singleton

B.register('laser')
B.register('xyz')

B.load('ccd.functions')

#---------------------------------------------------------------------------------

# focus min Canon

positions = {
    'A': {'x': 45.0, 'y': 45.0, 'z': 65.5},
    'B': {'x': 45.0, 'y': 36.0, 'z': 65.5},
    'C': {'x': 57.5, 'y': 40.0, 'z': 65.5},
    'D': {'x': 67.5, 'y': 16.0, 'z': 65.5}
    }

#---------------------------------------------------------------------------------

def cycles(self, angle = 0.0, exptime = 2.0, images = 20, cycles = 2):
    """
    Cycle sur les 4 positions pre-definies et prend 'images' images a chaque position.
    """

    for c in xrange(cycles):
        for pos in ['A', 'B', 'C', 'D']:
            self.log("Moving to position %s: %s" % (pos, str(positions[pos])))
            self.xyz.move(positions[pos])
            
            for i in xrange(images):
                meta = self.execute_reb_sequence('Acquisition', exptime=exptime)
                meta['xyz']['keys'].append('THETAPOS')
                meta['xyz']['values']['THETAPOS'] = float(angle)
                meta['xyz']['comments']['THETAPOS'] = '[deg] Current Theta position in degree'
                img = self.conv_to_fits()
                self.save_to_fits(img, meta)    

bench.Bench.cycles = cycles

#---------------------------------------------------------------------------------

