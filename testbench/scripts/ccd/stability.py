#! /usr/bin/env python
#
# LSST
# Stability with REB plus CCD.

import os
import time
import datetime
import astropy.io.fits as pyfits
from astropy.time import Time

from lsst.testbench.bench import Bench
from lsst.testbench.scripts.ccd.analysis import *

B = Bench()  # singleton

B.register('laser')
B.register('PhD')

def stability_monitor(self, iterate, channels, listexp):
    """
    Acquires repetitive data to monitor the stability.
    :return:
    """
    self.reb.set_testtype('STABILITY')
    self.reb.set_window(on=False)
    self.reb.reb.set_pointer('CleaningNumber', 2)  # works only on REBplus variants
    self.laser.select(2)
    self.laser.setCurrent(2, 50.0)
    self.laser.enable()


    fitsdir = os.path.join(self.reb.reb.fitstopdir, time.strftime('%Y%m%d', time.gmtime()), 'stability')
    if not os.path.isdir(fitsdir):
        os.makedirs(fitsdir)

    memfile = os.path.join(fitsdir, 'log.txt')
    f = open(memfile, 'a')
    f.write('File\tIphoto\tPlaser\tTASPICT\tTASPICB\tTREB7\tTREB9\n')

    for irepeat in xrange(iterate):
        for att in listexp:            
            try:
                m = self.execute_reb_sequence(name='Stripes', exptime=att, delaytime=4, withmeta=True)
            except:
                # breakup in communication
                time.sleep(60)
                m = self.execute_reb_sequence(name='Stripes', exptime=att, delaytime=4, withmeta=True)
            rawfile = self.reb.make_img_name()
            i = self.conv_to_fits(channels=channels, borders=True, imgname=rawfile, cleanup=True)  # need to manage disk space

            k1 = self.PhD.lastmeasure
            i[0].header['IPHOTO'] = k1

            s = '%d' % self.reb.stripe
            try:
                ttop = m['reb_ope']['values']['TREB_7']
                tbottom = m['reb_ope']['values']['TREB_9']
                m['LASER']['values']['POW_CH2']
                taspict = m['reb_ope']['values']['T_ASPT_2']
                taspicb = m['reb_ope']['values']['T_ASPB_2']
            except:
                ttop = 0
                tbottom = 0
                plaser = 0
                taspict = 0
                taspicb = 0

            self.save_to_fits(i, m, fitsname=self.reb.make_fits_name(imgstr=rawfile, compressed=True, fitsdir=fitsdir))

            f.write('%s\t%d\t%f\t%f\t%f\t%f\t%f\t%f\t' % (i[0].header['FILENAME'], att, k1, plaser, taspict, taspicb, ttop, tbottom))
            for name in find_channels(i, selectchannels=channels):
                img = i[name].data
                # stats on whole frame plus on 'stable' section
                light = img[50:, 50:95]
                dark = img[50:, 105:145]
                f.write('%10.2f\t%4.2f\t%10.2f\t%4.2f\t' % (dark.mean(), dark.std(), light.mean(), light.std()))
            f.write('\n')
            i.close()

    f.close()
    self.laser.disable()
    
Bench.stability_monitor = stability_monitor


