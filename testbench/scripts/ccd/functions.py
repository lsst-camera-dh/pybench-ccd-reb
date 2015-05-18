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
import py.testbench as testbench

B = testbench.Bench()  # singleton

B.register('reb')  # connect to the REB
B.register('bss')  # connect (remotely) to the BackSubstrate Power


def load_sequencer(self, filename=None):
    self.reb.load_sequencer(filename)

testbench.Bench.load_sequencer = load_sequencer


def REBpowerup(self):
    print("Powering up the REB1")
    self.reb.REBpowerup()

testbench.Bench.REBpowerup = REBpowerup


def CCDpowerup(self):
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

testbench.Bench.CCDpowerup = CCDpowerup


def CCDshutdown(self):
    print("Shutting down the CCD")
    self.reb.wait_end_sequencer()
    # Back-substrate first
    self.bss.disable()
    # TODO: wait until done
    time.sleep(10)
    self.reb.CCDshutdown()

testbench.Bench.CCDshutdown = CCDshutdown


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

    # get the rest from the instrument meta
    keys, values, comments = self.reb.get_meta()
    for key in keys:
        primaryhdu.header[key] = (values[key], comments[key])

    # CCD operating conditions
    exthdu = pyfits.ImageHDU(name="CCD_COND")
    keys, values, comments = self.reb.get_meta_operating()
    for key in keys:
        exthdu.header[key] = (values[key], comments[key])
    hdulist.append(exthdu)

    # Sequencer content
    seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=self.reb.get_meta_sequencer(),
                                                         ascii=True)])
    hdulist.append(seqhdu)

    hdulist.writeto(fitsname, clobber=True)
    print("Wrote FITS file "+fitsname)


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




# class Bench(object):
#     """
#     Internal representation of the full bench
#     """
#     opheader = {}
#     testheader = {}
#     primeheader = {}
#     reb_id = 2
#     strip_id = 0
#     nchannels = 16
#     imgtag = 0
#     xmlfile = "camera/reb/sequencer-soi.xml"
#     rawimgdir = "/home/lsst/test_images"
#     fitstopdir = "/home/lsst/test_frames"
#     logger = None  # update later if using logger
#     # The following should come from the XML file instead
#     imglines = 2020
#     imgcols = 550
#     exposuresub = "Exposure"
#     darksub = "DarkExposure"
#     exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
#     min_exposure = int(0.1 / exposure_unit)  # minimal duration of an exposure to avoid blocking shutter (not used for darks)
#     testtype = "Test"

#     def __init__(self, logger=None):
#         self.reb = reb.REB(reb_id=self.reb_id)
#         self.seq = reb.fromxmlfile(self.xmlfile)
#         self.primeheader["CTRLCFG"] = self.xmlfile
#         self.bss = BackSubstrate()  # logged in higher-level class k6487
#         self.temp = TempController(logger)
#         self.lamp = Source(logger)
#         self.monochromator = Monochromator(logger)



#     def 



#     def bench_shutdown(self):
#         pass
#         #self.lamp.ttl.closeShutter()


#     def get_headers(self):
#         """
#         Fills image header dictionaries for current setup.
#         """
#         #CCD operating conditions header
#         self.opheader = self.reb.get_operating_header()

#         self.opheader.update(self.bss.get_operating_header())
#         # TODO: power supply currents and voltages

#         #need to add instruments header, optional sequencer header
#         self.primeheader["WIDTH"] = self.imgcols
#         self.primeheader["HEIGHT"] = self.imglines
#         self.primeheader["DETSIZE"] = '[0:%d,0:%d]' % (self.imgcols*self.nchannels/2, 2*self.imglines)
#         self.primeheader["TESTTYPE"] = self.testtype
#         try:
#             wavelength = self.monochromator.getWavelength()
#         except:
#             wavelength = 0.0
#         self.primeheader["MONOWL"] = wavelength

#         self.monochromator.testheader["MONOWL"] = wavelength
#         self.primeheader["CCDTEMP"] = self.temp.getTemp()



#     def get_exposure_time(self, darktime=False):
#         """
#         Gets the exposure time from the subroutines in memory.
#         (input in seconds). If darktime is set to true, gives the dark 'exposure' time instead.
#         :param darktime: boolean
#         """

#         # look up address of exposure subroutine
#         # then get current instruction
#         if darktime:
#             darkadd = self.seq.program.subroutines[self.darksub]
#             instruction = self.seq.program.instructions[darkadd]
#         else:
#             exposureadd = self.seq.program.subroutines[self.exposuresub]
#             instruction = self.seq.program.instructions[exposureadd]
#         iter = instruction.repeat

#         return float(iter)*self.exposure_unit  # in seconds


#     def set_exposure_time(self, exptime, lighttime=True, darktime=True):
#         """
#         Modifies exposure subroutines to last the given exposure time
#         (input in seconds). By default both exposures with shutter open
#         and closed are modified, use optional parameters to preserve one
#         or the other.
#         :param exptime:
#         :param lighttime:
#         :param darktime:
#         """
#         newiter = int(exptime / self.exposure_unit)
#         # look up address of exposure subroutine
#         # then get current instruction and rewrite the number of iterations only
#         if lighttime:
#             exposureadd = self.seq.program.subroutines[self.exposuresub]
#             newinstruction = self.seq.program.instructions[exposureadd]
#             newinstruction.repeat = int(max(newiter, self.min_exposure))  # This does rewrite the seq.program too
#             self.reb.fpga.send_program_instruction(exposureadd, newinstruction)
#         #same for dark subroutine
#         if darktime:
#             darkadd = self.seq.program.subroutines[self.darksub]
#             newinstruction = self.seq.program.instructions[darkadd]
#             newinstruction.repeat = int(max(newiter, 1))  # must not be 0 or sequencer gets stuck
#             self.reb.fpga.send_program_instruction(darkadd, newinstruction)

#     def execute_sequence(self, name, exposuretime=None, waittime=20, fitsname=""):
#         """
#         Executing a 'main' sequence from the XML file or a subroutine, when sequencer is ready
#         :param self:
#         :param name: string

#         """

#         # Wait until sequencer is finished with current sequence
#         self.wait_end_sequencer()

#         # load new exposure time here (better: with XML parameter ?)
#         if exposuretime:
#             self.set_exposure_time(exposuretime)
#             exptime = exposuretime
#         # else use preset exposure time
#         else:
#             darktime = (name == "Dark")
#             exptime = self.get_exposure_time(darktime)

#         self.primeheader["DATE-OBS"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # acquisition date

#         self.reb.run_subroutine(name)

#         self.bss.start_monitor(exptime+4)  # time for clearing before exposure
#         self.lamp.start_monitor(exptime+4)
#         time.sleep(exptime + waittime)
#         self.primeheader["MONDIODE"] = self.lamp.read_monitor()

#         # check for output image
#         #getting tag from FPGA registers
#         hextag = self.reb.get_time()
#         imgname = os.path.join(self.rawimgdir,'0x%016x.img' % hextag)
#         if os.path.isfile(imgname):
#             self.get_headers()

#             if name == "Bias":
#                 self.primeheader["SHUT_DEL"] = 0
#             else:
#                 self.primeheader["SHUT_DEL"] = 100
#             self.primeheader["IMGTYPE"] = name
#             self.primeheader["EXPTIME"] = exptime
#             self.save_to_fits(imgname, fitsname)
#             # setting up tag for next image
#             self.update_tag(self.imgtag + 1)



#     def save_to_fits(self, imgname, fitsname = ""):
#         """
#         Turns img file from imageClient into FITS file.
#         """
#         # Reading raw file to array
#         dt = np.dtype('i4')
#         buff = np.fromfile(imgname, dtype=dt)
#         # negative numbers still need to be translated
#         #buffer = np.vectorize(lambda i: i - 0x40000 if i & (1 << 17) else i )(buff)
#         # also invert sign on all data
#         #buffer = np.vectorize(lambda i: 0x3FFFF-i if i & (1 << 17) else -i-1 )(buff)
#         # also make all values positive (to be tested)
#         # 0 -> 1FFFF, 1FFFF -> 0, 20000 -> 3FFFF, 3FFFF -> 20000
#         buffer = np.vectorize(lambda i: 0x5FFFF-i if i & (1 << 17) else 0x1FFFF-i)(buff)
#         # reshape by channel
#         length = self.imglines * self.imgcols
#         buffer = buffer.reshape(length, self.nchannels)

#         # Creating FITS HDUs:
#         # Create empty primary HDU and fills header
#         primaryhdu = pyfits.PrimaryHDU()
#         imgstr = os.path.splitext(os.path.basename(imgname))[0]
#         self.primeheader["IMAGETAG"] = imgstr
#         dict_to_fitshdu(self.primeheader, primaryhdu)
#         # also need info from 'localheader.txt'
#         localheader = pyfits.Header.fromtextfile("camera/localheader.txt")
#         primaryhdu.header.update(localheader)
#         # Create HDU list
#         hdulist = pyfits.HDUList([primaryhdu])

#         # Add extension for channels HDUs
#         for num in range(self.nchannels):
#             chan = buffer[0:length,num]
#             chan = chan.reshape(self.imglines, self.imgcols)
#             y = chan.astype(np.int32)
#             # create extension to fits file for each channel
#             exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
#             # exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
#             self.get_extension_header(num, exthdu)
#             avchan = np.mean(y[11:522,1:2002])
#             exthdu["AVERAGE"] = avchan
#             hdulist.append(exthdu)

#         # More header HDUs
#         exthdu = pyfits.ImageHDU(name="TEST_COND")
#         self.testheader.update(self.monochromator.testheader)
#         dict_to_fitshdu(self.testheader, exthdu)
#         hdulist.append(exthdu)
#         exthdu = pyfits.ImageHDU(name="CCD_COND")
#         dict_to_fitshdu(self.opheader,exthdu)
#         hdulist.append(exthdu)

#         # Sequencer dump
#         exthdu = get_sequencer_hdu(self.reb.fpga)
#         hdulist.append(exthdu)

#         # Writing file
#         if not fitsname:  # structure for specific tests
#             fitsname = self.make_fits_name(imgstr)
#         # else: using LSST scheme for directory and image name, already built in fitsname

#         primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
#         primaryhdu.header["DATE"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # FITS file creation date
#         hdulist.writeto(fitsname, clobber=True)

#         print("Wrote FITS file "+fitsname)

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


