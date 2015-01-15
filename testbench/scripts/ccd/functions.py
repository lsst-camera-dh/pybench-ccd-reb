# ! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import os
import types
import time
import datetime
#import subprocess
import numpy as np
import pyfits

import lsst.testbench

B = lsst.testbench.Bench() # singleton

# B.register('reb')  # connect to the REB 
# B.register('bss')  # connect (remotely) to the BackSubstrate Power

def load_sequencer(self):
    self.seq = reb.fromxmlfile(self.xmlfile)
    self.primeheader["CTRLCFG"] = self.xmlfile

    pass

# B.load_sequencer = types.MethodType(load_sequencer, B)
Bench.load_sequencer = load_sequencer

def CCDpowerup(self):
    print "Power up the CCD"
    pass

# B.CCDpowerup = types.MethodType(CCDpowerup, B)
Bench.CCDpowerup = CCDpowerup

# stand_alone = True

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


# def generate_frametag():
#     now = datetime.datetime.utcnow()
#     tagstr = time.strftime('%Y%m%d0%h%M%s', today) # + '%05d' % number
#     tag = int(tagstr,16)
#     return tag


# def log(name, logger, cmd, value = None):
#     """

#     :param name:
#     :param logger:
#     :param cmd:
#     :param value:
#     """
#     if logger:
#         if value:
#             logger.log("%s : %s = %s" % (name, str(cmd), str(value)) )
#         else:
#             logger.log("%s : %s" % (name, str(cmd)) )


# def dict_to_fitshdu(dictheader, fitshdu):
#     fitsheader = fitshdu.header
#     for keyword in dictheader:
#         fitsheader[keyword] = dictheader[keyword]


# def get_sequencer_hdu(fpga):
#     """
#     Builds table HDU for FITS file containing sequencer dump
#         :param fpga: FPGA
#         :return: pyfits.TableHDU
#         """
#     prog = fpga.dump_program()
#     progaddr = prog.instructions.keys()
#     prognum = 256 + len(progaddr)

#     slicenum = np.ndarray(shape=(prognum,), dtype=np.dtype('a4'))
#     output = np.ndarray(shape=(prognum,), dtype=np.dtype('a32'))
#     duration = np.ndarray(shape=(prognum,), dtype=np.dtype('i8'))

#     for ifunc in range(16):
#         seq = fpga.dump_function(ifunc)
#         for islice in range(16):
#             i = ifunc * 16 + islice
#             slicenum[i] = hex(i)[2:]
#             output[i] = bin(seq.outputs[islice])[2:]
#             duration[i] = seq.timelengths[islice]

#     for i, addr in enumerate(sorted(progaddr)):
#         slicenum[i+256] = '30' + hex(addr)[2:]
#         output[i+256] = prog.instructions[addr].__repr__()[:20]
#         duration[i+256] = prog.instructions[addr].repeat

#     slicecol = pyfits.Column(name="Address", format='A4', array=slicenum)
#     outputcol = pyfits.Column(name="Output", format='A32', array=output)
#     durationcol = pyfits.Column(name="Time", format='I8', array=duration)

#     exthdu = pyfits.new_table([slicecol, outputcol, durationcol], tbtype='TableHDU')
#     # add name to extension here
#     exthdu.header["EXTNAME"] = "SEQ_CFG"

#     return exthdu


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


#     def REBpowerup(self):
#         """
#         Operations after powering the REB (through CCS)
#         :return:
#         """
#         try:
#             self.reb.read(0, 5)
#         except:
#             wait_for_action("Could not establish communication with DREB, try rebooting RCE.")
#             self.reb.read(0, 5)

#         self.reb.set_strip(self.strip_id)
#         self.reb.cabac_reset()
#         self.reb.send_sequencer(self.seq)
#         hextag = generate_tag(self.imgtag)
#         self.reb.set_time(hextag)  # using time registers to store image tag (do not run clock in this case)
#         #self.CCDshutdown()

#         print("REB ready to connect to CCD")
#         #subprocess.Popen("imageClient %d" % self.reb_id, shell=True)  # hijacks the ipython shell
#         print("Remember to launch imageClient in %s" % self.rawimgdir)

#     def CCDpowerup(self):
#         """
#         Sequence to power up the CCD safely.
#         """

#         #sets the default sequencer clock states to 0
#         self.reb.send_function(0, reb.Function( name="default state",
#                                                 timelengths={0: 2, 1: 0},
#                                                 outputs={0: 0, 1: 0} ))

#         #starting drain voltages on CABAC
#         drains = {"OD": 29, "GD": 24, "RD": 18}
#         self.reb.send_cabac_config(drains)

#         time.sleep(1)

#         #starting OG voltage on CABAC
#         og = {"OG": 3.5}
#         self.reb.send_cabac_config(og)

#         time.sleep(1)

#         #sets clock rails
#         dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
#         self.reb.set_dacs(dacs)

#         time.sleep(1)

#         #sets clock currents on CABAC
#         iclock = {"IC": 255}
#         self.reb.send_cabac_config(iclock)

#         time.sleep(1)

#         #puts current on CS gate
#         dacOS = {"I_OS": 0xfff}
#         self.reb.set_dacs(dacOS)

#         #rewrite default state of sequencer (to avoid reloading functions)
#         self.reb.send_function(0, reb.Function( name="default state",
#                                             timelengths={0: 2, 1: 0},
#                                             outputs={0: 0x6bc, 1: 0} ))

#         time.sleep(1)

#         #starts Keithley backsubstrate voltage
#         self.bss.config(voltage=-40)
#         self.bss.enable()

#         print("Start-up sequence complete")

#     def CCDshutdown(self):
#         """
#         Sequence to shut down the CCD safely
#         """

#         self.wait_end_sequencer()
#         #Back-substrate first
#         self.bss.disable()

#         #current source
#         self.reb.set_dacs({"I_OS": 0})

#         time.sleep(1)

#         #clock states to 0 
#         self.reb.send_function(0, reb.Function( name="default state",
#                                                 timelengths={0: 2, 1: 0},
#                                                 outputs={0: 0, 1: 0} ))
#         #currents on CABAC clocks to 0
#         self.reb.send_cabac_config({"IC": 0})
#         #clock rails to 0
#         self.reb.set_dacs({"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0})

#         time.sleep(1)

#         #currents on OG to 0
#         self.reb.send_cabac_config({"OG": 0})

#         time.sleep(1)

#         #drains to 0
#         self.reb.send_cabac_config({"OD": 0, "GD": 0, "RD": 0})

#         print("CCD shutdown complete")

#     def bench_shutdown(self):
#         pass
#         #self.lamp.ttl.closeShutter()

#     def update_tag(self, num = 1):
#         """
#         Updates the clock tag to current date and given sequence number
#         :param num: int
#         :return:
#         """
#         self.imgtag = num
#         hextag = generate_tag(self.imgtag)
#         self.reb.set_time(hextag)

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

#     def get_extension_header(self, REBchannel, fitshdu, borders = False):
#         """
#         Builds FITS extension header with position information for each channel
#         :param REBchannel: int
#         :return:
#         """
#         extheader = fitshdu.header
#         extheader["NAXIS1"] = self.imgcols
#         extheader["NAXIS2"] = self.imglines

#         if borders == False:
#             parstringlow = '1:2002'
#             parstringhigh = '4004:2003'
#             colwidth = 512
#             extheader['DETSIZE'] = '[1:4096,1:4004]'
#             extheader['DATASEC'] = '[11:522,1:2002]'
#         else :
#             parstringlow = '1:%d' % self.imglines
#             parstringhigh = '%d:%d' % (2*self.imglines, self.imglines+1)
#             colwidth = self.imgcols
#             extheader['DETSIZE'] = self.primeheader["DETSIZE"]
#             extheader['DATASEC'] = '[1:%d,1:%d]' % (self.imgcols, self.imglines)

#         if REBchannel<self.nchannels/2:
#             pdet = parstringlow
#             si = colwidth*(REBchannel+1)
#             sf = colwidth*REBchannel+1
#         else :
#             pdet = parstringhigh
#             # previous geometry
#             #si = colwidth*(self.nchannels-1-REBchannel)+1
#             #sf = colwidth*(self.nchannels-REBchannel)
#             si = colwidth*(REBchannel-self.nchannels/2)+1
#             sf = colwidth*(REBchannel-self.nchannels/2+1)

#         extheader['DETSEC'] = '[%d:%d,%s]' % (si,sf,pdet)

#     def waiting_sequence(self, name="Wait"):
#         """
#         Lets CCD wait until keyboard interrupt is sent by clearing periodically

#         """
#         self.wait_end_sequencer()
#         keepwaiting = True
#         while keepwaiting:
#             try:
#                 self.reb.run_subroutine(name)
#                 time.sleep(60)
#             except KeyboardInterrupt:
#                 keepwaiting = False

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

#     def wait_end_sequencer(self):
#         """
#         Waits until the sequencer is not running anymore.
#         """
#         while self.reb.get_state() & 4:  # sequencer status bit in the register
#             time.sleep(1)

#     def make_fits_name(self, imgstr):
#         fitsdir = os.path.join(self.fitstopdir,time.strftime('%Y%m%d',time.gmtime()))
#         if not os.path.isdir(fitsdir):
#             os.mkdir(fitsdir)
#         fitsname = os.path.join(fitsdir, imgstr +'.fits')
#         return fitsname

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
#     b.waiting_sequence()
#     return b


