# ! /usr/bin/env python
#
# LSST
#
# Basic functions using REB and BSS Keithley to manage the CCD.
# 

import os
import time
import datetime
import logging
import astropy.io.fits as pyfits
from astropy.time import Time

#reload(lsst.testbench.scripts.ccd.functions)

from lsst.testbench.bench import Bench

B = Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('bss')  # connect (remotely) to the BackSubstrate Power
# B.register('PhD')


def load_sequencer(self, filename=None):
    """
    Loads the functions and the program from a file (default file for this REB if none given).
    """
    self.reb.load_sequencer(filename)

Bench.load_sequencer = load_sequencer


def initialize_REB(self):
    """
    Puts REB in a state where it is ready to be connected to a CCD (for REB1)
    or where it is ready to start the CCD power-up (WREB).
    :return:
    """
    # TODO : add power supplies here for controlled power-up

    # replicate some operations done at object initialization
    # (covers cases when REB has been rebooted but not Python)
    self.reb.set_stripe(self.reb.stripe)
    self.reb.update_filetag()

    if not self.bss.voltageStatus():
        self.reb.REBpowerup()
    else:
        logging.info("Back-Substrate is enabled, we should not be in this state when executing intitialize_REB")

Bench.initialize_REB = initialize_REB


def shutdown_REB(self):
    """
    Shuts down the REB.
    For REB1, it does nothing, but should include the power supplies shutdown.
    For WREB, it starts shutting down power to the CABACs, and should be followed by power supplies shutdown.
    :return:
    """
    if not self.bss.voltageStatus():
        self.reb.REBshutdown()
    else:
        logging.info("Back-Substrate is enabled, we should not be in this state when executing shutdown_REB")

    # TODO: need to add power supplies here for shutdown

Bench.shutdown_REB = shutdown_REB

def setup_BSS(self):
    """
    Does setup operations for BSS, only if it is not enabled.
    :param self:
    :return:
    """
    if not self.bss.voltageStatus():
        # reset only if not enabled
        self.bss.send('*RST')
        # reset is apparently needed before configuring (otherwise error 16 pops up)
        self.bss.setup(voltage=-60)
        # self.bss.setup_current_measure(2e-5)
        self.bss.setup_current_measure(2e-4)
        logging.info('Done BSS setup')
    else:
        logging.info('Could not perform BSS setup, was already ON')

Bench.setup_BSS = setup_BSS


def powerup_CCD(self):
    """
    CCD complete power-up sequence with REB and back-substrate.
    :return:
    """
    logging.info("Starting CCD power-up sequence")
    self.reb.CCDpowerup()
    time.sleep(1)

    self.setup_BSS()
    # starts Keithley backsubstrate voltage
    self.bss.enable(delay=10.0)
    # TODO: wait until complete
    logging.info("CCD start-up sequence is complete")

    #configure default frame and starts waiting sequence
    self.reb.set_window(on=False)
    self.reb.start_waiting_sequence()

Bench.powerup_CCD = powerup_CCD


def shutdown_CCD(self):
    """
    CCD complete shutdown sequence with REB and back-substrate.
    :return:
    """
    logging.info("Starting CCD shut-down sequence")
    self.reb.stop_waiting_sequence()  # in case it was in waiting loop
    self.reb.wait_end_sequencer()
    # Back-substrate first
    self.bss.disable()
    self.reb.CCDshutdown()
    logging.info("CCD shut-down sequence is complete")

Bench.shutdown_CCD = shutdown_CCD


def execute_reb_sequence(self, name='', exptime=None, delaytime=4, withclap=True, withmeta=True):
    """
    Configure new REB sequence if name and/or exptime are given.
    Executes the sequence.
    Acquires meta parameters if withmeta is True.
    :return: dict
    """
    self.reb.stop_waiting_sequence()  # in case it was in waiting loop
    
    if name and exptime:
        self.reb.config_sequence(name, exptime)
    elif name:
        self.reb.config_sequence(name)
    else:
        # waits until the sequencer stops (included when configuring the sequence)
        self.reb.wait_end_sequencer()

    # Here execute, for all instruments, the pre_exposure functions
    self.pre_exposure(exptime)
    
    # ... then send the execute sequence command 
    self.reb.execute_sequence()
    # delay for clear before exposure
    time.sleep(delaytime)

    # delay for exposure
    time.sleep(self.reb.reb.exptime)

    # Here execute, for all instruments, the post_exposure functions
    self.post_exposure()

    # delay for readout
    time.sleep(4.0)
    
    meta = {}
    if withmeta:
        # meta from all instruments
        meta = self.get_meta()
        # additionnal meta from REB
        keys, values, comments = self.reb.get_meta_operating()
        meta['reb_ope'] = {'extname': 'CCD_COND',
                           'keys': keys,
                           'values': values,
                           'comments': comments,
                           'data': []}  # added data for compatibility with the rest of the meta
    return meta

Bench.execute_reb_sequence = execute_reb_sequence


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


def conv_to_fits(self, channels=None, borders=False, imgname=None, cleanup=False):
    """
    Converts the given raw image to FITS data.
    :rtype: pyfits.HDUlist
    """
    if imgname:
        rawfile = imgname
    else:
        rawfile = self.reb.make_img_name()

    if not os.path.isfile(rawfile):
        logging.info("Did not find the expected raw file: %s " % rawfile)

    hdulist = self.reb.conv_to_fits(rawfile, channels, displayborders=borders)

    if cleanup:
        os.remove(rawfile)

    return hdulist

Bench.conv_to_fits = conv_to_fits


def eotest_header(hdulist):
    """
    FITS headers: add specific parameters to primary, 'CCD_COND' and 'TEST_COND'.
    :param self:
    :param hdulist:
    :rtype: pyfits.ImageHDU
    """
    # Test conditions (instruments other than REB)
    testhdu = pyfits.ImageHDU(name='TEST_COND')
    primaryhdu = hdulist[0]

    if 'BSS' in hdulist:
        if hdulist['BSS'].header['VOLTSRC']:  # if it is activated
            hdulist['CCD_COND'].header['V_BSS'] = (hdulist['BSS'].header['VOLTAGE'], '[V] Keithley Back-Substrate voltage')
        else:
            hdulist['CCD_COND'].header['V_BSS'] = (0.0, '[V] Keithley Back-Substrate voltage')
        hdulist['CCD_COND'].header['I_BSS'] = (hdulist['BSS'].header['CURRENT'], '[A] Keithley Back-Substrate current')
    if 'TRIAX' in hdulist:
        primaryhdu.header['MONOWL'] = (hdulist['TRIAX'].header['WVLGTH'], '[nm] Monochromator wavelength')
    elif 'CORNERSTONE' in hdulist:
        primaryhdu.header['MONOWL'] = (hdulist['CORNERSTONE'].header['WVLGTH'], '[nm] Monochromator wavelength')
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

    return testhdu


def save_to_fits(self, hdulist, meta={}, fitsname='', LSSTstyle = True):
    """
    Saves the given FITS HDUlist to a file with auxiliary headers for instruments parameters.
    """
    if not fitsname:
        fitsname = self.reb.make_fits_name(self.reb.make_img_name(), compressed=True)

    primaryhdu = hdulist[0]

    # one extension per instrument
    for identifier in meta:
        instrumentmeta = meta[identifier]
        extname = instrumentmeta['extname']
        values = instrumentmeta['values']
        if extname in ['REB', 'REB2']:
            append_kvc(primaryhdu, instrumentmeta['keys'], values, instrumentmeta['comments'])
        else:
            exthdu = pyfits.ImageHDU(data=instrumentmeta['data'], name=extname)
            append_kvc(exthdu, instrumentmeta['keys'], values, instrumentmeta['comments'])
            hdulist.append(exthdu)
            
    # appending more keywords to primary header
    primaryhdu.header["FILENAME"] = (os.path.basename(fitsname), 'Original name of the file')
    primaryhdu.header["DATE"] = (datetime.datetime.utcnow().isoformat(), 'FITS file creation date')
    obstime = primaryhdu.header["DATE-OBS"]
    primaryhdu.header["MJD-OBS"] = (Time(obstime).mjd, 'Modified Julian Date of image acquisition')

    # if LSSTstyle,
    if LSSTstyle and meta:
        testhdu = eotest_header(hdulist)
        hdulist.append(testhdu)

    # Sequencer content
    seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=self.reb.get_meta_sequencer(),
                                                         ascii=True)])
    seqhdu.header['EXTNAME'] = 'SEQUENCER'
    hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True, checksum=True)
    logging.info("Wrote FITS file "+fitsname)

Bench.save_to_fits = save_to_fits


# def wait_for_action(action):
#     """
#     Pause the execution until the specified action has been recorded as 'done' by the user.
#     :param action:basic_stats
#     """
#     print(action)
#     s = ""
#     while s != "done":
#         s = raw_input("Type 'done' when complete --> ")
#         s = s.lower()




