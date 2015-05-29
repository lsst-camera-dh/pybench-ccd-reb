# ! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts
# Here we should put the basic functions that use several instruments
# of the bench.

import os
import time
import logging
import astropy.io.fits as pyfits

#reload(lsst.testbench.scripts.ccd.functions)

#import py.testbench.bench as bench
import lsst.testbench.bench as bench

B = bench.Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('bss')  # connect (remotely) to the BackSubstrate Power


def load_sequencer(self, filename=None):
    self.reb.load_sequencer(filename)

bench.Bench.load_sequencer = load_sequencer


def initialize_REB(self):
    self.reb.REBpowerup()

bench.Bench.initialize_REB = initialize_REB


def powerup_CCD(self):
    logging.info("Starting CCD power-up sequence")
    self.reb.CCDpowerup()
    time.sleep(1)
    # starts Keithley backsubstrate voltage
    if not self.bss.voltageStatus():
        # reset only if not enabled
        self.bss.send('*RST')
        # reset is apparently needed before configuring (otherwise error 16 pops up)
        self.bss.setup(voltage=-60)
        self.bss.setup_current_measure(2e-5)
    self.bss.enable(delay=20.0)
    # TODO: wait until complete
    logging.info("CCD start-up sequence is complete")
    self.reb.waiting_sequence()

bench.Bench.powerup_CCD = powerup_CCD


def shutdown_CCD(self):
    print("Starting CCD shut-down sequence")
    self.reb.wait_end_sequencer()
    # Back-substrate first
    self.bss.disable()
    # extra wait time for safety
    time.sleep(10)
    self.reb.CCDshutdown()
    logging.info("CCD shut-down sequence is complete")

bench.Bench.shutdown_CCD = shutdown_CCD


def execute_reb_sequence(self, withmeta=True, name='', exptime=None):
    """
    Configure new REB sequence if name and/or exptime are given.
    Executes the sequence.
    Acquires meta parameters if withmeta is True.
    """
    if name and exptime:
        self.reb.config_sequence(name, exptime)
    elif name:
        self.reb.config_sequence(name)
        
    self.reb.execute_sequence()
    
    meta = {}
    if withmeta:
        # meta from all instruments
        meta = self.get_meta()
        # additionnal meta from REB
        keys, values, comments = self.reb.get_meta_operating()
        meta['reb_ope'] = {'extname': 'CCD_COND',
                           'keys': keys,
                           'values': values,
                           'comments': comments}
    return meta

bench.Bench.execute_reb_sequence = execute_reb_sequence


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


def conv_to_fits(self, channels=None, imgname=None):
    """
    Converts the given raw image to FITS data.
    """
    if imgname:
        rawfile = imgname
    else:
        rawfile = self.reb.make_img_name()

    if not os.path.isfile(rawfile):
        print("Did not find the expected raw file: %s " % rawfile)

    hdulist = self.reb.conv_to_fits(rawfile, channels)

    return hdulist

bench.Bench.conv_to_fits = conv_to_fits


def save_to_fits(self, hdulist, meta, fitsname='', LSSTstyle = True):
    """
    Saves the given FITS HDUlist to a file with auxiliary headers for instruments parameters.
    """
    if not fitsname:
        fitsname = self.reb.make_fits_name(self.reb.make_img_name())

    primaryhdu = hdulist[0]

    # appending more keywords to header
    primaryhdu.header["FILENAME"] = (os.path.basename(fitsname), 'FITS file name')
    primaryhdu.header["DATE"] = (time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), 'FITS file creation date')

    # one extension per instrument
    for identifier in meta:
        instrumentmeta = meta[identifier]
        extname = instrumentmeta['extname']
        values = instrumentmeta['values']
        exthdu = pyfits.ImageHDU(name=extname)
        append_kvc(exthdu, instrumentmeta['keys'], values, instrumentmeta['comments'])
        hdulist.append(exthdu)
        

    # if LSSTstyle, add specific parameters to primary, 'CCD_COND' and 'TEST_COND'
    if LSSTstyle:
        # Test conditions (instruments other than REB)
        testhdu = pyfits.ImageHDU(name='TEST_COND')

        if 'BSS' in hdulist:
            if hdulist['BSS'].header['VOLTSRC']:  # if it is activated
                hdulist['CCD_COND'].header['V_BSS'] = (hdulist['BSS'].header['VOLTAGE'], '[V] Keithley Back-Substrate voltage')
            else:
                hdulist['CCD_COND'].header['V_BSS'] = (0.0, '[V] Keithley Back-Substrate voltage')
            hdulist['CCD_COND'].header['I_BSS'] = (hdulist['BSS'].header['CURRENT'], '[A] Keithley Back-Substrate current')
        if 'TRIAX' in hdulist:  # TODO: to be updated with Newport
            primaryhdu.header['MONOWL'] = (hdulist['TRIAX'].header['WVLGTH'], '[nm] Monochromator wavelength')
            # add to testhdu
            # replace with laser wavelength if laser is connected
        if 'LAKESHORE0' in hdulist:
            primaryhdu.header['CCDTEMP'] = (hdulist['LAKESHORE0'].header['TEMPA'], '[C] CCD temperature')
        elif 'LAKESHORE1' in hdulist:
            primaryhdu.header['CCDTEMP'] = (hdulist['LAKESHORE1'].header['TEMPA'], '[C] CCD temperature')
            # also need 'TEMP_SET' for primaryhdu, not yet available in thermal_lakeshore
        if 'TTL' in hdulist:
            primaryhdu.header['FILTER'] = (hdulist['TTL'].header['LMPFILT'], 'Filter wheel position')
            # TODO: add conversion to filter reference
        for extname in ['QTH', 'XEHG']:
            if extname in hdulist:
                testhdu.header['SRCTYPE'] = (extname, 'Source type')
                if hdulist[extname].header['ON']:
                    testhdu.header['SRCPWR'] = (hdulist[extname].header['POWER'], '[W] Lamp power')
                else:
                    testhdu.header['SRCPWR'] = (0, '[W] Lamp power')
        if 'LASER' in hdulist:
            # currently no parameter to know which channels are enabled
            testhdu.header['SRCTYPE'] = ('LASER', 'Source type')
            for chan in range(1,5):
                keylaser = 'POW_CH%d' % chan
                testhdu.header[keylaser] = hdulist['LASER'].header[keylaser]
        if 'PHD' in hdulist:
            testhdu.header['MONDIODE'] = (hdulist['PHD'].header['CURRENT'], '[A] Monitoring photodiode current')

        hdulist.append(testhdu)

    # Sequencer content
    seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=self.reb.get_meta_sequencer(),
                                                         ascii=True)])
    seqhdu.header['EXTNAME'] = 'SEQUENCER'
    hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True)
    logging.info("Wrote FITS file "+fitsname)

bench.Bench.save_to_fits = save_to_fits



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


