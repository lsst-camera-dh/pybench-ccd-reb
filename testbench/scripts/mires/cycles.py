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
import datetime

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

def mire_cycles(self, angle = 0.0, exptime = 0.75, images = 20, cycles = 2, view=False):
    """
    Cycle sur les 4 positions pre-definies et prend 'images' images a chaque position.
    """

    if view:
        import pyds9
        myds9 = pyds9.DS9("zorglub")

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

                if view:
                    filename = os.path.join('/data/frames', 
                                            datetime.datetime.utcnow().date().isoformat().replace('-',''),
                                            img[0].header['FILENAME'])
                    myds9.set("file mosaicimage iraf %s" % filename)

                # tentative pour limiter les fuites de memoire...
                for hdu in img: del hdu
                del img

                    

bench.Bench.mire_cycles = mire_cycles

#---------------------------------------------------------------------------------

def mire_biases(self, images = 20):

    self.laser.disable()
    print "Pensez a eteindre la lumiere car il n'y a pas d'obturateur... et il y a des fuites... (wait 5s)"
    time.sleep(5)

    for i in xrange(images): 
        meta = self.execute_reb_sequence('AcquireBias')
        meta['reb']['values']['TESTTYPE'] = 'BOXDARK'

        img = self.conv_to_fits()
        self.save_to_fits(img, meta)
        # tentative pour limiter les fuites de memoire...
        for hdu in img: del hdu
        del img

bench.Bench.mire_biases = mire_biases


#---------------------------------------------------------------------------------

def mire_program(self, angle = 0.0, exptime = 0.75, images = 20, cycles = 2, 
                 laserchannel = 2, lasercurrent = 50.0,
                 view=False):

    self.log("Taking %d biases..." % images)

    self.laser.disable()
    self.mire_biases(images = images)

    self.log("Taking %d images in the 4 positions..." % images)

    for c in self.laser.allchannels:
        self.laser.unselect(c)

    self.laser.select(laserchannel)
    self.laser.setCurrent(laserchannel, lasercurrent)
    self.laser.enable()
    time.sleep(5)

    self.mire_cycles(angle = angle, exptime = exptime, images = images, cycles = cycles, view=view)

    self.log("The End.")

    self.laser.disable()

bench.Bench.mire_program = mire_program

#---------------------------------------------------------------------------------

