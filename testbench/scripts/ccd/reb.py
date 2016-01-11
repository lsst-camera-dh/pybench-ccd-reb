# ! /usr/bin/env python
#
# LSST
#
# Basic functions to test the REB only.
# Replicates a lot from ccd.functions to test the functions before plugging the CCD in.
# Could split this into tests and REB functions, use REB functions in both ccd.functions and in linearity test.

import os
import time
import datetime
import astropy.io.fits as pyfits

from lsst.testbench.bench import Bench
from lsst.testbench.scripts.ccd.analysis import *

B = Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('attenuator')


#load_sequencer(self, filename=None):
# B.reb.load_sequencer(filename)

# def initialize_REB(self):
#B.reb.REBpowerup()


# def shutdown_REB(self):
# B.reb.REBshutdown()

# def powerup_CCD(self):
# B.reb.CCDpowerup()

#def shutdown_CCD(self):
# B.reb.wait_end_sequencer()
# B.reb.CCDshutdown()

def execute_reb_sequence(self, name='', exptime=None, delaytime=4, withmeta=True):
    """
    Configure new REB sequence if name and/or exptime are given.
    Executes the sequence.
    Acquires meta parameters if withmeta is True.
    :return: dict
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

    # delay for readout
    time.sleep(4.0)
    
    meta = {}
    if withmeta:
        # meta from all instruments
        meta = self.get_meta()
        # additionnal meta from REB, removed temporarily for speed
        #keys, values, comments = self.reb.get_meta_operating()
        #meta['reb_ope'] = {'extname': 'CCD_COND',
        #                   'keys': keys,
        #                   'values': values,
        #                   'comments': comments,
        #                   'data': []}  # added data for compatibility with the rest of the meta
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


def conv_to_fits(self, channels=None, borders=False, imgname=None):
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

    return hdulist

Bench.conv_to_fits = conv_to_fits


def save_to_fits(self, hdulist, meta={}, fitsname=''):
    """
    Saves the given FITS HDUlist to a file with auxiliary headers for instruments parameters.
    """
    if not fitsname:
        fitsname = self.reb.make_fits_name(self.reb.make_img_name(), compressed=True)

    primaryhdu = hdulist[0]

    # appending more keywords to header
    primaryhdu.header["FILENAME"] = (os.path.basename(fitsname), 'Original name of the file')
    primaryhdu.header["DATE"] = (datetime.datetime.utcnow().isoformat(), 'FITS file creation date')

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

    #if LSSTstyle and meta:
    #    testhdu = eotest_header(hdulist)
    #    hdulist.append(testhdu)

    # Sequencer content, removed for speed
    #seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
    #                                                     array=self.reb.get_meta_sequencer(),
    #                                                     ascii=True)])
    #seqhdu.header['EXTNAME'] = 'SEQUENCER'
    #hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True, checksum=True)
    logging.info("Wrote FITS file "+fitsname)

Bench.save_to_fits = save_to_fits


def linearity_scan(self, start=0, start6=30, end=50, localdir='linearity', sourcechan=None):
    """
    Acquires data for a linearity scan with the programmable attenuator.
    :type self: Bench
    :param att:
    :return:
    """
    self.reb.set_testtype('LINEARITY')
    fitsdir = os.path.join(self.reb.reb.fitstopdir, time.strftime('%Y%m%d', time.gmtime()), localdir)
    if not os.path.isdir(fitsdir):
            os.makedirs(fitsdir)

    # list of values
    listdB = range(start, start6)
    listdB.extend(range(start6, end, step=6))

    for att in listdB:
        #
        self.attenuator.set_attenuation(att)
        m = self.execute_reb_sequence(name='Bias', delaytime=2, withmeta=True)
        i = self.conv_to_fits(borders=True)
        # TODO: do a voltage measure outside of running time
        k = 0
        # k = self.
        i[0].header['ATT'] = att
        i[0].header['VOLT'] = k

        # option 1: check baseline and pulse amplitude (roughly)
        self.attenuator.set_attenuation(127)
        # TODO: volt measure
        i[0].header['VOLTBASE'] = 0
        self.attenuator.set_attenuation(0)
        # TODO: volt measure
        i[0].header['ATT0'] = 0

        self.save_to_fits(i, m, fitsname=os.path.join(fitsdir, 'reb3-dB%d.fz' % att))

        # TODO: better estimate than k
        if sourcechan is None:
            memfile = os.path.join(fitsdir, 'recap.txt')
            f = open(memfile, 'a')
            f.write('%d\t%f\t' % (att, k))
            for name in find_channels(i):
                img = i[name].data
                light = img[500:, 20:]
                f.write('%10.2f\t%4.2f\t' % (light.mean(), light.std()))
            f.write('\n')
        else:
            memfile = os.path.join(fitsdir, 'xtalk_memory.txt')
            f = open(memfile, 'a')
            f.write('%d\t%f\n' % (att, k))
            f.close()
            xtalk_memory(i, sourcechan, 50000, outfilename=memfile)
        i.close()

        # option 2: acquire baseline file

Bench.linearity_scan = linearity_scan

