# ! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import time
from datetime import date
import os
import subprocess
import xmlrpclib
import reb
import fpga
import xml
import numpy as np
import pyfits

def wait_for_action(action):
    """
    Pause the execution until the specified action has been recorded as 'done' by the user.
    :param action:
    """
    print(action)
    s = ""
    while s != "done":
        s = raw_input("Type 'done' when complete --> ")
        s = s.lower()


def generate_tag(number):
    today = date.today()
    tagstr = today.strftime('%Y%m%d')+'%05d' % number
    tag = int(tagstr,16)
    return tag


def dict_to_fitshdu(dictheader, fitshdu):
    fitsheader = fitshdu.header
    for keyword in dictheader:
        fitsheader[keyword] = dictheader[keyword]


class Bench(object):
    """
    Internal representation of the full bench
    """
    opheader = {}
    testheader = {}
    primeheader = {}
    sequencerheader = {}
    slitsize = 30
    reb_id = 2
    setvoltbss = 40
    nchannels = 16
    imgtag = 0
    xmlfile = "camera/reb/sequencer-soi.xml"
    # The following should come from the XML file instead
    imglines = 2020
    imgcols = 550
    detsize = '[0:4400,0:4040]'
    exposureadd = 0x3000d0 # depends on XML loading, tbc
    exposurereg = 0x16000000 # call to exposure function
    testtype = "Test"

    def __init__(self):
        self.reb = reb.REB(reb_id=self.reb_id)
        self.seq = xml.fromxmlfile(self.xmlfile)
        self.primeheader["CTRLCFG"] = self.xmlfile
        self.bss = xmlrpclib.ServerProxy("http://lpnlsst:8087/")# wrong
        self.bss.connect()
        self.multi = xmlrpclib.ServerProxy("http://lpnlsst:8087/")  # OK
        self.ttl = xmlrpclib.ServerProxy("http://lpnlsst:8083/")  # OK
        self.ttl.connect()
        # light sources: create objects here, does not try to connect
        self.qth = xmlrpclib.ServerProxy("http://lpnlsst:")  # TBC
        self.xehg = xmlrpclib.ServerProxy("http://lpnlsst:8089/")  # TBC
        self.triax = xmlrpclib.ServerProxy("http://lpnlsst:8086/")  # OK
        self.laser = xmlrpclib.ServerProxy("http://lpnlsst:8082/")  # TBC

    def REBpowerup(self):
        """
        Operations after powering the REB (through CCS)
        :return:
        """
        try:
            self.reb.fpga.read(0, 5)
        except:
            wait_for_action("Could not establish communication with DREB, try rebooting RCE.")
            self.reb.fpga.read(0, 5)

        self.reb.send_sequencer(self.seq)
        hextag = generate_tag(self.imgtag)
        self.reb.fpga.set_time(hextag)  # using time registers to store image tag (do not run clock in this case)
        self.CCDshutdown()

        print("REB ready to connect to CCD")
        #subprocess.Popen("imageClient %d" % self.reb_id, shell=True)  # hijacks the ipython shell

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """

        #sets the default sequencer clock states to 0
        self.reb.send_function(0, fpga.Function(name="default state",
                                                timelengths={0: 2, 1: 0},
                                                outputs={0: 0, 1: 0}))

        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.reb.set_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG": 3.5}
        self.reb.set_cabac_config(og)

        time.sleep(1)

        #sets clock rails
        dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
        self.reb.set_dacs(dacs)

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.reb.set_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS": 0xfff}
        self.reb.set_dacs(dacOS)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.reb.send_function(0, fpga.Function(name="default state",
                                                timelengths={0: 2, 1: 0},
                                                outputs={0: 0x6bc, 1: 0}))

        time.sleep(1)

        #starts Keithley backsubstrate voltage
        self.config_bss(self.setvoltbss)
        self.bss.setVoltageOperate(1)
        while abs(self.bss.getVoltage() - self.setvoltbss) > 0.1:
            time.sleep(1)

        print("Start-up sequence complete")

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """

        self.wait_end_sequencer()
        #Back-substrate first
        self.bss.setVoltageOperate(0)

        while abs(self.bss.getVoltage()) > 0.1:
            time.sleep(1)

        #current source
        self.reb.set_dacs({"I_OS": 0})

        time.sleep(1)

        #clock states to 0
        self.reb.send_function(0, fpga.Function(name="default state",
                                                timelengths={0: 2, 1: 0},
                                                outputs={0: 0, 1: 0}))
        #currents on CABAC clocks to 0
        self.reb.set_cabac_config({"IC": 0})
        #clock rails to 0
        self.reb.set_dacs({"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0})

        time.sleep(1)

        #currents on OG to 0
        self.reb.set_cabac_config({"OG": 0})

        time.sleep(1)

        #drains to 0
        self.reb.set_cabac_config({"OD": 0, "GD": 0, "RD": 0})

        print("CCD shutdown complete")

    def bench_shutdown(self):
        self.ttl.closeShutter()

    def config_bss(self, voltage=40):
        """
        Configuration of Keithley 6487 used to generate back-substrate voltage.
        """

        if voltage < 50:
            range = 50.0
        else:
            range = 500.0
        self.bss.selectOutputVoltageRange(range, 2.5e-5)

        self.bss.setOutputVoltage(voltage)

        self.bss.zeroCorrect()
        self.bss.selectCurrent(2e-5)

    def set_slit_size(self, slitsize):
        """
        Sets both slit sizes on the monochromator and waits until complete
        :param slitsize:
        :return:
        """
        self.slitsize = slitsize
        self.triax.setInSlit(self.slitsize)
        while self.triax.status() == 0:
            time.sleep(1.0)
        self.triax.setOutSlit(self.slitsize)
        while self.triax.status() == 0:
            time.sleep(1.0)

    def move_to_wavelength(self, wavelength, SelectGrating=False):
        """
            Moves the monochromator to the selected wavelength and waits until it is done.
            Calculates automatically which grating to use if authorized to change.
            """
        if SelectGrating:
            if wavelength < 800:
                grating = 0
                lines = 1198
            elif wavelength < 1400:
                grating = 1
                lines = 599
            else:
                grating = 2
                lines = 599  # TODO: check values
            self.triax.setGrating(grating) 
            self.testheader["MONOPOS"] = grating
            self.testheader["MONOGRAT"] = lines

        self.triax.setWavelength(wavelength)
        while self.triax.status() == 0:
            time.sleep(1.0)

    def select_source(self, sourcetype, wavelength=500.0):
        """
            Connects and starts whichever light source is going to be used
            """
        if sourcetype == "Fe55":
            pass  # will be motorized at some point
        elif sourcetype == "laser":
            self.laser.connect()
            # TODO: selects output based on wavelength
        elif sourcetype == "qth":
            self.ttl.openShutter()
            self.ttl.selectQTH()
            self.qth.connect()
            # TODO: start lamp here
        elif sourcetype == "xehg":
            self.ttl.openShutter()
            self.ttl.selectXeHg()
            self.xehg.connect()
            # TODO: start lamp here
        else:
            raise IOError("Unknown type of source")
        self.testheader["SRCTYPE"] = sourcetype.upper()
        #self.testheader["SCRMODL"]  # source model
        #self.testheader["SRCPWR"]  # source power in Watts

        if sourcetype in ["qth", "xehg"]:
            self.triax.connect()
            self.move_to_wavelength(wavelength, True)
            self.set_slit_size(self.slitsize)
        self.testheader["MONOTYPE"] = "Triax180"

        self.multi.connect()
        if self.multi.checkConnection() != '6514':
            print("Incorrect connection to Keithley 6514 multimeter")

    def get_headers(self):
        """
            Fills image header dictionaries for current setup.
            """
        #CCD operating conditions header
        self.opheader = self.reb.get_operating_header()

        self.opheader["V_BSS"] = "{:.2f}".format(self.bss.getOutputVoltage())
        # gives only current at this time, might upgrade to get measures during exposure
        self.opheader["I_BSS"] = "{:.2f}".format(self.bss.getCurrent())
        # TODO: power supply currents and voltages

        #need to add instruments header, optional sequencer header
        self.primeheader["WIDTH"] = self.imgcols
        self.primeheader["HEIGHT"] = self.imglines
        self.primeheader["DETSIZE"] = self.detsize
        self.primeheader["TESTTYPE"] = self.testtype
        try:
            wavelength = self.triax.getWavelength()
        except:
            wavelength = 0.0
        self.primeheader["MONOWL"] = wavelength

        self.testheader["MONOWL"] = wavelength
        #TODO: temperature

    def get_extension_header(self, REBchannel, fitshdu, borders = False):
        """
        Builds FITS extension header with position information for each channel
        :param REBchannel:
        :return:
        """
        extheader = fitshdu.header
        extheader["NAXIS1"] = self.imgcols
        extheader["NAXIS2"] = self.imglines

        if borders == False:
            parstringlow = '1:2002'
            parstringhigh = '4004:2003'
            colwidth = 512
            extheader['DETSIZE'] = '[1:4096,1:4004]'
            extheader['DATASEC'] = '[11:522,1:2002]'
        else :
            parstringlow = '1:2020'
            parstringhigh = '4040:2021'
            colwidth = self.imgcols
            extheader['DETSIZE'] = self.detsize
            extheader['DATASEC'] = '[1:550,1:2020]'

        if REBchannel<self.nchannels/2:
            pdet = parstringlow
            si = colwidth*(REBchannel+1)
            sf = colwidth*REBchannel+1
        else :
            pdet = parstringhigh
            si = colwidth*(self.nchannels-REBchannel)+1
            sf = colwidth*(self.nchannels-REBchannel+1)

        extheader['DETSEC'] = '[{}:{},{}]'.format(si,sf,pdet)


    def execute_sequence(self, name, exposuretime = 2, waittime=15, number=1):
        """
            Executing a 'main' sequence from the XML file or a subroutine, when sequencer is ready
            :param self:
            :param name: sequence name in the XML
            :param number: number of times to execute (if calling a subroutine)
            """
        # TODO: Check that both options work

        # Wait until sequencer is finished with current sequence
        self.wait_end_sequencer()

        # load new exposure time here (better: with XML parameter ?)
        self.reb.fpga.write(self.exposureadd, self.exposurereg + int(exposuretime * 1000))
        self.primeheader["DATE-OBS"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # acquisition date

        if number > 1:
            self.reb.run_subroutine(name, repeat=number)
        else:
            self.reb.run_subroutine(name)

        time.sleep(exposuretime + waittime)

        # check for output image
        #getting tag from FPGA registers
        hextag = self.reb.fpga.get_time()
        imgname = '0x%016x.img' % hextag
        if os.path.isfile(imgname):
            self.get_headers()

            if name == "Bias":
                self.primeheader["SHUT_DEL"] = 0
            else:
                self.primeheader["SHUT_DEL"] = 100
            self.primeheader["IMGTYPE"] = name
            self.primeheader["EXPTIME"] = exposuretime
            self.save_to_fits(imgname)
            self.imgtag = self.imgtag + 1
            hextag = generate_tag(self.imgtag)
            self.reb.fpga.set_time(hextag)  # setting up tag for next image

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.reb.fpga.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def save_to_fits(self, imgname):
        """
        Turns img file from imageClient into FITS file.
        """
        # Reading raw file to array
        dt = np.dtype('i4')
        buff = np.fromfile(imgname, dtype=dt)
        # negative numbers still need to be translated
        buffer = np.vectorize(lambda i: i - 0x40000 if i & (1 << 17) else i )(buff)
        # reshape by channel
        length = self.imglines * self.imgcols
        buffer = buffer.reshape(length, self.nchannels)

        # Creating FITS HDUs:
        # Create empty primary HDU and fills header
        primaryhdu = pyfits.PrimaryHDU()
        self.primeheader["DATE"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # FITS file creation date
        # more keywords ?
        dict_to_fitshdu(self.primeheader, primaryhdu)
        # also need info from 'localheader.txt'
        localheader = pyfits.Header.fromtextfile("/home/lsst/ccd_scripts/headers/localheader.txt")
        primaryhdu.header.update(localheader)
        # Create HDU list
        hdulist = pyfits.HDUList([primaryhdu])

        # Add extension for channels HDUs
        for num in range(self.nchannels):
            chan = buffer[0:length,num]
            chan = chan.reshape(self.imglines, self.imgcols)
            y = chan.astype(np.int32)
            #creates extension to fits file
            exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)
            self.get_extension_header(num, exthdu)
            hdulist.append(exthdu)

        # More header HDUs
        exthdu = pyfits.BinTableHDU(name="TEST_COND")
        dict_to_fitshdu(self.testheader,exthdu)
        hdulist.append(exthdu)
        exthdu = pyfits.BinTableHDU(name="CCD_COND")
        dict_to_fitshdu(self.opheader,exthdu)
        hdulist.append(exthdu)

        # Sequencer dump
        #slicenum = pyfits.Column(name="Slice", format='A2', array=)
        #exthdu = pyfits.new_table([slicenum, output, duration], tbtype='TableHDU')
        #hdulist.append(exthdu)

        # Writing file
        # TODO: compression
        datedir = "/home/lsst/test_frames/"+ date.today().strftime('%Y%m%d')
        if not os.path.isdir(datedir):
            #creates directory for that date
            os.mkdir(datedir)
        fitsname = os.path.join(datedir,os.path.splitext(imgname)[0])+'.fits' # TODO: names with test types
        hdulist.writeto(fitsname, clobber=True)

        print("Wrote FITS file "+fitsname)

if __name__ == '__main__':

    bench = Bench()
    bench.REBpowerup()
    wait_for_action("REB can be connected to CCD now.")
    bench.CCDpowerup()
    # Puts CCD in waiting state by clearing periodically, while waiting for a new command.
    while True:
        bench.execute_sequence("Wait", waittime=60)

