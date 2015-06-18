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

import lsst.testbench.bench as bench

B = bench.Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('bss')  # connect (remotely) to the BackSubstrate Power
# B.register('PhD')

def load_sequencer(self, filename=None):
    self.reb.load_sequencer(filename)

bench.Bench.load_sequencer = load_sequencer


def initialize_REB(self):
    self.reb.REBpowerup()

bench.Bench.initialize_REB = initialize_REB


def shutdown_REB(self):
    self.reb.REBshutdown()
    # TODO: need to add power supplies here for WREB shutdown

bench.Bench.shutdown_REB = shutdown_REB


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
    #do that after
    #proc = self.reb.start_waiting_sequence()

bench.Bench.powerup_CCD = powerup_CCD


def shutdown_CCD(self):
    logging.info("Starting CCD shut-down sequence")
    self.reb.wait_end_sequencer()
    # Back-substrate first
    self.bss.disable()
    # extra wait time for safety
    time.sleep(10)
    self.reb.CCDshutdown()
    logging.info("CCD shut-down sequence is complete")

bench.Bench.shutdown_CCD = shutdown_CCD


def execute_reb_sequence(self, name='', exptime=None, delaytime=4, withclap=True, withmeta=True):
    """
    Configure new REB sequence if name and/or exptime are given.
    Executes the sequence.
    Acquires meta parameters if withmeta is True.
    """
    if name and exptime:
        self.reb.config_sequence(name, exptime)
    elif name:
        self.reb.config_sequence(name)
       
    # this waits until the sequencer stops...
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

    # self.PhD.read_measurement() -> transfered in post exposure hook

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


def conv_to_fits(self, channels=None, borders=False, imgname=None):
    """
    Converts the given raw image to FITS data.
    """
    if imgname:
        rawfile = imgname
    else:
        rawfile = self.reb.make_img_name()

    if not os.path.isfile(rawfile):
        logging.info("Did not find the expected raw file: %s " % rawfile)

    hdulist = self.reb.conv_to_fits(rawfile, channels, displayborders=borders)

    return hdulist

bench.Bench.conv_to_fits = conv_to_fits


def save_to_fits(self, hdulist, meta={}, fitsname='', LSSTstyle = True):
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
        if extname == 'REB':
            append_kvc(primaryhdu, instrumentmeta['keys'], values, instrumentmeta['comments'])
        else:
            exthdu = pyfits.ImageHDU(data=instrumentmeta['data'], name=extname)
            append_kvc(exthdu, instrumentmeta['keys'], values, instrumentmeta['comments'])
            hdulist.append(exthdu)

    # if LSSTstyle, add specific parameters to primary, 'CCD_COND' and 'TEST_COND'
    if LSSTstyle and meta:
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

def basic_stats(self, hdulist, logtofile=False):
    """
    Basic statistics on the frame from the fits HDUlist. 
    Printed to screen and saved to a txt file.
    Appends estimated values to the fits extension header.
    """
    summaryfile = "stats_"+time.strftime("%Y%m%d",time.localtime())+".txt"
    if logtofile:
        logger = open(summaryfile, 'a')

    print("Channel\t MeanLight  SdevLight   MeanOverS   SdevOverS   MeanOverP   SdevOverP")
    for ichan in range(16):
        name = "CHAN_%d" % ichan
        if name not in hdulist:
            continue
        hdr = hdulist[name].header
        img = hdulist[name].data
        imgcols = 512
        colstart = 10
        imglines = 2002
        light = img[:imglines, colstart:colstart+imgcols].flatten()
        dark = img[:imglines, colstart+imgcols:].flatten()
        overp = img[imglines+2:, colstart:].flatten()
        
        hdr['AVLIGHT'] = light.mean()
        hdr['STDLIGHT'] = light.std()
        hdr['AVOVERS'] = dark.mean()
        hdr['STDOVERS'] = dark.std()
        hdr['AVOVERP'] = overp.mean()
        hdr['STDOVERP'] = overp.std()
        
        out = "{}\t{:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f} {:10.2f}".format(name,
                                                                                 hdr['AVLIGHT'], hdr['STDLIGHT'],
                                                                                 hdr['AVOVERS'], hdr['STDOVERS'],
                                                                                 hdr['AVOVERP'], hdr['STDOVERP'])
        print(out)
        if logtofile:
            logger.write(out+'\n')
    #return out

bench.Bench.basic_stats = basic_stats

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


