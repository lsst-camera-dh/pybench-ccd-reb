# ! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts
# Here we should put the basic functions that use several instruments
# of the bench.

import os
import time
import numpy as np
import astropy.io.fits as pyfits

#import py.testbench.drivers.ccd_reb as reb
#import py.testbench.bench as bench
import lsst.testbench.bench as bench

B = bench.Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('bss')  # connect (remotely) to the BackSubstrate Power


def load_sequencer(self, filename=None):
    self.reb.load_sequencer(filename)

bench.Bench.load_sequencer = load_sequencer


def initialize_REB(self):
    print("Powering up the REB1")
    self.reb.REBpowerup()

bench.Bench.initialize_REB = initialize_REB


def powerup_CCD(self):
    print "Powering up the CCD"
    self.reb.CCDpowerup()
    time.sleep(1)
    # starts Keithley backsubstrate voltage
    self.bss.config(voltage=-60)
    self.bss.enable()
    # TODO: wait until complete, checks
    time.sleep(5)
    print("Start-up sequence complete")
    self.reb.waiting_sequence()

bench.Bench.powerup_CCD = powerup_CCD


def shutdown_CCD(self):
    print("Shutting down the CCD")
    self.reb.wait_end_sequencer()
    # Back-substrate first
    self.bss.disable()
    # TODO: wait until done
    time.sleep(10)
    self.reb.CCDshutdown()

bench.Bench.shutdown_CCD = shutdown_CCD


# this should be moved to a more generic package
def append_kvc(exthdu, keys, values, comments):
    """
    Appends the keywords to the header of exthdu
    :param exthdu:
    :param keys:
    :param values:
    :param comments:
    :return:
    """
    for key in keys:
        exthdu.header[key] = (values[key], comments[key])


def save_to_fits(self, channels=None, imgname=None, fitsname=''):
    """
    Saves the given raw image to FITS file with all auxiliary headers.
    Note: does not include incrementing on FPGA image tag. Should be done
    afterwards if successful and if we want to keep the raw data.
    """
    if imgname:
        rawfile = imgname
    else:
        rawfile = self.reb.make_img_name()

    if not os.path.isfile(rawfile):
        print("Did not find the expected raw file: %s " % rawfile)

    if not fitsname:
        fitsname = self.reb.make_fits_name(rawfile)

    hdulist = self.reb.conv_to_fits(rawfile, channels)
    primaryhdu = hdulist[0]

    primaryhdu.header["FILENAME"] = (os.path.basename(fitsname), 'FITS file name')
    primaryhdu.header["DATE"] = (time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), 'FITS file creation date')
    primaryhdu.header["TESTTYPE"] = ('TEST', 'TEST:DARK:FLAT:OBS:PPUMP:QE:SFLAT')

    # CCD operating conditions
    exthdu = pyfits.ImageHDU(name="CCD_COND")
    keys, values, comments = self.reb.get_meta_operating()
    append_kvc(exthdu, keys, values, comments)

    # get the rest from the instrument meta of all registered bench instruments
    meta = self.get_meta()
    for identifier in meta:
        instrumentmeta = meta[identifier]
        if instrumentmeta['extname'] == 'BSS':
            append_kvc(exthdu, instrumentmeta['keys'], instrumentmeta['values'], instrumentmeta['comments'])
        # if too many keywords: will sort into another extension header named "TEST_COND"
        else:
            append_kvc(primaryhdu, instrumentmeta['keys'], instrumentmeta['values'], instrumentmeta['comments'])

    # Sequencer content
    seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=self.reb.get_meta_sequencer(),
                                                         ascii=True)])
    seqhdu['NAME'] = 'SEQUENCER'

    hdulist.append(exthdu)
    hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True)
    print("Wrote FITS file "+fitsname)

bench.Bench.save_to_fits = save_to_fits


    # more stuff to put here

    #TEMP_SET	-95.00
    #CCDTEMP	-95.12
    #MONDIODE	143.12
    #MONOWL	550.00
    #FILTER	'550LP'


# def wait_for_action(action):
#     """
#     Pause the execution until the specified action has been recorded as 'done' by the user.
#     :param action:
#     """
#     print(action)
#     s = ""
#     while s != "done":
#         s = raw_input("Type 'done' when complete --> ")
#         s = s.lower()



# def start():
#     """
#     Bench start-up operations strung together.

#     :return: Bench
#     """
#     b = Bench()
#     b.REBpowerup()
#     wait_for_action("REB can be connected to CCD now.")
#     b.CCDpowerup()
#     # Puts CCD in waiting state by clearing periodically, while waiting for a new command.
#
#     return b


