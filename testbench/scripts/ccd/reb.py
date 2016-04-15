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

B.register('reb2')  # connect to the REB
B.register('attenuator')
B.register('Vkeithley')
B.Vkeithley.setup(1)

#load_sequencer(self, filename=None):
# B.reb2.load_sequencer(filename)

# def initialize_REB(self):
#B.reb2.REBpowerup()


# def shutdown_REB(self):
# B.reb2.REBshutdown()

# def powerup_CCD(self):
# B.reb2.CCDpowerup()
# B.reb2.set_parameter('RGU', 5)

#def shutdown_CCD(self):
# B.reb2.wait_end_sequencer()
# B.reb2.CCDshutdown()

def execute_reb_sequence(self, name='', exptime=None, delaytime=4, withmeta=True):
    """
    Configure new REB sequence if name and/or exptime are given.
    Executes the sequence.
    Acquires meta parameters if withmeta is True.
    :return: dict
    """
    if name and exptime:
        self.reb2.config_sequence(name, exptime)
    elif name:
        self.reb2.reb.select_subroutine(name)
        self.reb2.reb.shutdelay = 0
        self.reb2.reb.exptime = 0

    # this waits until the sequencer stops...
    self.reb2.wait_end_sequencer()

    # Here execute, for all instruments, the pre_exposure functions
    self.pre_exposure(exptime)
    
    # ... then send the execute sequence command 
    self.reb2.execute_sequence()
    # delay for clear before exposure
    time.sleep(delaytime)

    # delay for exposure
    time.sleep(self.reb2.reb.exptime)

    # Here execute, for all instruments, the post_exposure functions
    self.post_exposure()

    # delay for readout
    time.sleep(5.0)
    
    meta = {}
    if withmeta:
        # meta from all instruments
        meta = self.get_meta()
        # additionnal meta from REB, can be removed for speed
        keys, values, comments = self.reb2.get_meta_operating()
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
        rawfile = self.reb2.make_img_name()

    if not os.path.isfile(rawfile):
        logging.info("Did not find the expected raw file: %s " % rawfile)

    hdulist = self.reb2.conv_to_fits(rawfile, channels, displayborders=borders)

    if cleanup:
        os.remove(rawfile)

    return hdulist

Bench.conv_to_fits = conv_to_fits


def save_to_fits(self, hdulist, meta={}, fitsname=''):
    """
    Saves the given FITS HDUlist to a file with auxiliary headers for instruments parameters.
    """
    if not fitsname:
        fitsname = self.reb2.make_fits_name(self.reb2.make_img_name(), compressed=True)

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
    #                                                     array=self.reb2.get_meta_sequencer(),
    #                                                     ascii=True)])
    #seqhdu.header['EXTNAME'] = 'SEQUENCER'
    #hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True, checksum=True)
    print("Wrote FITS file "+fitsname)

Bench.save_to_fits = save_to_fits


def linearity_scan(self, start=0, start6=30, end=50, localdir='linearity', sourcechan=None):
    """
    Acquires data for a linearity scan with the programmable attenuator.
    :type self: Bench
    :param att:
    :return:
    """

    self.reb2.set_testtype('LINEARITY')
    fitsdir = os.path.join(self.reb2.reb.fitstopdir, time.strftime('%Y%m%d', time.gmtime()), localdir)
    if not os.path.isdir(fitsdir):
        os.makedirs(fitsdir)

    # list of values
    listdB = range(start, start6)
    listdB.extend(range(start6, end, 6))

    if sourcechan is None:
        memfile = os.path.join(fitsdir, 'recap.txt')     
    else:
        memfile = os.path.join(fitsdir, 'xtalk_memory_ch%d.txt' % sourcechan)
    f = open(memfile, 'a')
    f.write('dB\tVoltPre\tVoltPost\tVolt0\tVolt127\n')
    
    for att in listdB:
        self.attenuator.set_attenuation(att)
        #m = self.execute_reb_sequence(name='Bias', delaytime=4, withmeta=True)
        m = self.execute_reb_sequence(name='Window', delaytime=4, withmeta=True)
        i = self.conv_to_fits(borders=True)

        i[0].header['ATT'] = att
        k1 = self.Vkeithley.v1
        i[0].header['VOLT1'] = k1
        k2 = self.Vkeithley.v2
        i[0].header['VOLT2'] = k2

        # option 1: check baseline and pulse amplitude (roughly)
        self.attenuator.set_attenuation(127)
        time.sleep(4)
        k127 = self.Vkeithley.get_voltage_median(5)
        i[0].header['VOLTBASE'] = k127
        self.attenuator.set_attenuation(0)
        time.sleep(4)
        k0 = self.Vkeithley.get_voltage_median(5)
        i[0].header['ATT0'] = k0

        self.save_to_fits(i, m, fitsname=os.path.join(fitsdir, 'reb3-dB%d.fz' % att))

        f.write('%d\t%f\t%f\t%f\t%f\t' % (att, k1, k2, k0, k127))
        if sourcechan is None:
            for name in find_channels(i):
                img = i[name].data
                light = img[500:, 20:]
                f.write('%10.2f\t%4.2f\t' % (light.mean(), light.std()))
            f.write('\n')
        else:
            f.write('\n')
            try:
                xtalk_memory(i, sourcechan, 35000, f)
            except:
                print('Stopping at %d dB' % att)
                break  # too low to detect pulses
        i.close()

        # option 2: acquire baseline file and reference file
    f.close()
    
Bench.linearity_scan = linearity_scan


def stability_monitor(self, iterate, channels):
    """
    Acquires repetitive data to monitor the stability.
    :param self:
    :param iterate:
    :return:
    """
    self.reb2.set_testtype('STABILITY')
    self.reb2.config_sequence('Acquisition', exptime=15.0)
    self.reb2.reb.set_pointer('CleaningNumber', 0)  # works only on REBplus variants

    fitsdir = os.path.join(self.reb2.reb.fitstopdir, time.strftime('%Y%m%d', time.gmtime()), 'stability')
    if not os.path.isdir(fitsdir):
        os.makedirs(fitsdir)

    memfile = os.path.join(fitsdir, 'log.txt')
    f = open(memfile, 'a')
    f.write('File\tVoltPre\tVoltPost\tTaspicT\tTaspicB\n')

    for irepeat in xrange(iterate):
        m = self.execute_reb_sequence(delaytime=0, withmeta=True)
        rawfile = self.reb2.make_img_name()
        i = self.conv_to_fits(channels=channels, borders=True, imgname=rawfile, cleanup=True)  # need to manage disk space

        k1 = self.Vkeithley.v1
        i[0].header['VOLT1'] = k1
        k2 = self.Vkeithley.v2
        i[0].header['VOLT2'] = k2
        s = '%d' % self.reb2.stripe
        try:
            ttop = m['reb_ope']['values']['T_ASPT_' + s]
            tbottom = m['reb_ope']['values']['T_ASPB_' + s]
        except:
            ttop = 0
            tbottom = 0

        self.save_to_fits(i, m, fitsname=self.reb2.make_fits_name(imgstr=rawfile, compressed=True, fitsdir=fitsdir))

        f.write('%s\t%f\t%f\t%f\t%f\t' % (i[0].header['FILENAME'], k1, k2, ttop, tbottom))
        for name in find_channels(i, selectchannels=channels):
            img = i[name].data
            # stats on whole frame plus on 'stable' section
            light = img[500:, 20:]
            f.write('%10.2f\t%4.2f\t%10.2f\t%4.2f\t' % (img.mean(), img.std(), light.mean(), light.std()))
        f.write('\n')
        i.close()

    f.close()

Bench.stability_monitor = stability_monitor


