# ! /usr/bin/env python
#
# LSST
#
# Testing a Python class to replace CCD bench scripts

import time
from datetime import date
import os
#import subprocess
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


def log(name, logger, cmd, value = None):
    """

    :param name:
    :param logger:
    :param cmd:
    :param value:
    """
    if logger:
        if value:
            logger.log("%s : %s = %s" % (name, str(cmd), str(value)) )
        else:
            logger.log("%s : %s" % (name, str(cmd)) )


def dict_to_fitshdu(dictheader, fitshdu):
    fitsheader = fitshdu.header
    for keyword in dictheader:
        fitsheader[keyword] = dictheader[keyword]


def get_sequencer_hdu(fpga):
    """
    Builds table HDU for FITS file containing sequencer dump
        :param fpga: FPGA
        :return: pyfits.TableHDU
        """
    prog = fpga.dump_program()
    progaddr = prog.instructions.keys()
    prognum = 256 + len(progaddr)
    slicenum = np.ndarray(shape=(prognum,), dtype=np.dtype('a4'))
    output = np.ndarray(shape=(prognum,), dtype=np.dtype('a32'))
    duration = np.ndarray(shape=(prognum,), dtype=np.dtype('i8'))
    for ifunc in range(16):
        for islice in range(16):
            seq = fpga.dump_function(ifunc)
            i = ifunc * 16 + islice
            slicenum[i] = hex(i)[2:]
            output[i] = bin(seq.outputs[islice])[2:]
            duration = seq.timelengths[islice]
    for i, addr in enumerate(sorted(progaddr)):
        slicenum[i+256] = '30' + hex(addr)[2:]
        output[i+256] = prog.instructions[addr].__repr__()[:20]
        duration[i+256] = prog.instructions[addr].repeat

    slicecol = pyfits.Column(name="Address", format='A2', array=slicenum)
    outputcol = pyfits.Column(name="Output", format='A32', array=output)
    durationcol = pyfits.Column(name="Time", format='I8', array=duration)

    exthdu = pyfits.TableHDU(pyfits.FITS_rec.from_columns([slicecol, outputcol, durationcol]), name="SEQ_DUMP")

    return exthdu


class XMLRPC(object):
    """
    Generic class to manage objects connected through XMLRPC
    """

    def __init__(self, server, idstr, name):
        self.name = name
        self.server = server
        self.idstr = idstr
        self.comm = xmlrpclib.ServerProxy(self.server)

    def connect(self):
        self.comm.connect()
        checkstr = self.comm.checkConnection()
        if checkstr != self.idstr:
            print("Incorrect connection to %s, returns %s " % (self.name, checkstr))


class BackSubstrate(XMLRPC):
    """
    Managing back-substrate voltage controlled by Keithley 6487
    """
    setvoltbss = 0  # desired voltage setting (independent of actual value)

    def __init__(self):
        XMLRPC.__init__(self, server="http://lpnlsst:8087/", idstr="6487", name="Keithley 6487")

    def connect(self):
        XMLRPC.connect(self)

    def config(self, voltage=0):
        """
        Configuration of voltage, current limits and current readout.
        """

        if abs(voltage) < 50:
            range = 50.0
        else:
            range = 500.0
        self.comm.selectOutputVoltageRange(range, 2.5e-5)

        if voltage < 0:
            self.comm.setOutputVoltage(float(voltage))
            self.setvoltbss = voltage
        else:
            raise ValueError("Asked for a positive back-substrate voltage (%f), not doing it. " % voltage)

        self.comm.zeroCorrect()
        self.comm.selectCurrent(2e-5)

    def set_volt(self, voltage):
        """
        Changes voltage without changing configuration
        """
        if voltage < 0:
            self.comm.setOutputVoltage(float(voltage))
            self.setvoltbss = voltage
        else:
            raise ValueError("Asked for a positive back-substrate voltage (%f), not doing it. " % voltage)

        while abs(self.comm.getVoltage() - self.setvoltbss) > 0.1:
            time.sleep(1)

    def enable(self):

        self.comm.setVoltageOperate(1)
        while abs(self.comm.getVoltage() - self.setvoltbss) > 0.1:
            time.sleep(1)

    def disable(self):

        self.comm.setVoltageOperate(0)
        while abs(self.comm.getVoltage() - 0) > 0.1:
            time.sleep(1)


class Source(object):
    """
    Management of the light sources and iron 55 source.
    """
    source_selector = ("Fe55", "XeHg", "QTH", "Laser")
    lamp_list = ["XeHg", "QTH"]

    def __init__(self, logger=None):
        self.source_name = None
        self.laser = XMLRPC("http://lpnlsst:8082/", "TBC", "Laser Thorlab") # TBC
        self.ttl = XMLRPC("http://lpnlsst:8083/","TBC","TTL")  # OK
        self.ttl.connect()
        # light sources: create objects here, does not try to connect
        self.qth = XMLRPC("http://lpnlsst:","TBC", "QTH lamp")  # TBC
        self.xehg = XMLRPC("http://lpnlsst:8089/", "TBC", "XeHg lamp")  # TBC
        self.logger = logger

    def select_source(self, sourcetype):

        if sourcetype == "Fe55":
            pass  # will be motorized at some point
        elif sourcetype == "Laser":
            self.laser.connect()
            # TODO: selects output based on wavelength
        elif sourcetype == "QTH":
            self.ttl.comm.selectQTH()
            self.qth.connect()
            # TODO: start lamp here
        elif sourcetype == "XeHg":
            self.ttl.comm.selectXeHg()
            self.xehg.connect()
            # TODO: start lamp here
        else:
            raise IOError("Unknown type of source")
        self.source_name = sourcetype

    def getWatts(self):
        if self.source_name == "Fe55":
            return None
        else:
            pass
            #self.logger.log("%s : Watts = %f" % (self.source_name, value) )

    def setWatts(self, power):
        # TODO
        log(self.source_name, self.logger, "Set Watts", power)

    def getAlim(self):
        """
        Current limit on lamps.
        """
        if self.source_name == "XeHg":
            return self.xehg.comm.getPresetCurrent()

        return None

    def on(self):
        if self.source_name in self.lamp_list:
            self.ttl.comm.openShutter()
        if self.source_name == "XeHg":
            self.xehg.power(1)
        # TODO: other types
        log(self.source_name, self.logger, "On")

    def off(self):
        if self.source_name in self.lamp_list:
            self.ttl.comm.closeShutter()
        if self.source_name == "XeHg":
            self.xehg.power(0)
        log(self.source_name, self.logger, "Off")


class Monochromator(object):
    """
    Management of monochromator and input filter
    """
    testheader = {}
    slitsize = 30

    def __init__(self, logger=None):
        self.triax = XMLRPC("http://lpnlsst:8086/", "1", "Triax 180")  # idstr TBC
        # TODO: add filter management
        self.logger = logger

    def connect(self):
        self.triax.connect()

    def set_slit_size(self, slitsize):
        """
        Sets both slit sizes on the monochromator and waits until complete
        :param slitsize:
        :return:
        """
        self.slitsize = slitsize
        self.triax.comm.setInSlit(self.slitsize)
        while self.triax.comm.status() == 0:
            time.sleep(1.0)
        self.triax.comm.setOutSlit(self.slitsize)
        while self.triax.comm.status() == 0:
            time.sleep(1.0)

    def setWavelength(self, wavelength, SelectGrating=False):
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
            self.triax.comm.setGrating(grating)
            self.testheader["MONOPOS"] = grating
            self.testheader["MONOGRAT"] = lines

        self.triax.comm.setWavelength(wavelength)
        while self.triax.comm.status() == 0:
            time.sleep(1.0)
        log(self.triax.name, "setWavelength", wl)

    def setFilter(self, value):
        pass


class Bench(object):
    """
    Internal representation of the full bench
    """
    opheader = {}
    testheader = {}
    primeheader = {}
    reb_id = 2
    nchannels = 16
    imgtag = 0
    xmlfile = "camera/reb/sequencer-soi.xml"
    rawimgdir = "/home/lsst/test_images"
    fitstopdir = "/home/lsst/test_frames"
    logger = None  # update later if using logger
    # The following should come from the XML file instead
    imglines = 2020
    imgcols = 550
    detsize = '[0:4400,0:4040]'
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    testtype = "Test"
    sensorID = "100-00"
    teststamp = time.strftime("%Y%m%d-%H%M%S",time.localtime())  # to be renewed at each test series

    def __init__(self, logger=None):
        self.reb = reb.REB(reb_id=self.reb_id)
        self.seq = xml.fromxmlfile(self.xmlfile)
        self.primeheader["CTRLCFG"] = self.xmlfile
        self.bss = BackSubstrate()  # logged in higher-level class k6487
        self.bss.connect()
        self.lamp = Source(logger)
        self.monochromator = Monochromator(logger)
        self.multi = xmlrpclib.ServerProxy("http://lpnlsst:8087/")  # To be changed: 6487 should be here

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
        print("Remember to launch imageClient in %s" % self.rawimgdir)

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
        self.bss.config(voltage=-40)
        self.bss.enable()

        print("Start-up sequence complete")

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """

        self.wait_end_sequencer()
        #Back-substrate first
        self.bss.disable()

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
        self.lamp.ttl.comm.closeShutter()

    def select_source(self, sourcetype, wavelength=500.0):
        """
            Connects and starts whichever light source is going to be used
            """
        self.lamp.select_source(sourcetype)
        self.testheader["SRCTYPE"] = sourcetype.upper()
        #self.testheader["SCRMODL"]  # source model
        self.testheader["SRCPWR"] = self.lamp.getWatts()

        if sourcetype in self.lamp.lamp_list:
            self.monochromator.connect()
            self.monochromator.setWavelength(wavelength, True)
            self.monochromator.set_slit_size(30)
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

        self.opheader["V_BSS"] = "{:.2f}".format(self.bss.comm.getOutputVoltage())
        # gives only current at this time, might upgrade to get measures during exposure
        self.opheader["I_BSS"] = "{:.2f}".format(self.bss.comm.getCurrent())
        # TODO: power supply currents and voltages

        #need to add instruments header, optional sequencer header
        self.primeheader["WIDTH"] = self.imgcols
        self.primeheader["HEIGHT"] = self.imglines
        self.primeheader["DETSIZE"] = self.detsize
        self.primeheader["TESTTYPE"] = self.testtype
        try:
            wavelength = self.monochromator.triax.comm.getWavelength()
        except:
            wavelength = 0.0
        self.primeheader["MONOWL"] = wavelength

        self.monochromator.testheader["MONOWL"] = wavelength
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

    def waiting_sequence(self, name="Wait"):
        """
        Lets CCD wait until keyboard interrupt is sent by clearing periodically

        """
        self.wait_end_sequencer()
        keepwaiting = True
        while keepwaiting:
            try:
                self.reb.run_subroutine(name)
                time.sleep(60)
            except KeyboardInterrupt:
                keepwaiting = False

    def set_exposure_time(self, exptime, lighttime=True, darktime=True):
        """
        Modifies exposure subroutines to last the given exposure time
        (input in seconds). By default both exposures with shutter open
        and closed are modified, use optional parameters to preserve one
        or the other.
        :param exptime:
        :param lighttime:
        :param darktime:
        """
        newiter = int(exptime * 1000)  # Exposures iterate over 1ms subroutines
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        if lighttime:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            newinstruction = self.seq.program.instructions[exposureadd]
            newinstruction.repeat = newiter  # This does rewrite the seq.program too
            self.reb.fpga.send_program_instruction(exposureadd, newinstruction)
        #same for dark subroutine
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            newinstruction = self.seq.program.instructions[darkadd]
            newinstruction.repeat = newiter
            self.reb.fpga.send_program_instruction(darkadd, newinstruction)

    def execute_sequence(self, name, exposuretime=2, waittime=15, fitsname=""):
        """
            Executing a 'main' sequence from the XML file or a subroutine, when sequencer is ready
            :param self:
            :param name: string

            """

        # Wait until sequencer is finished with current sequence
        self.wait_end_sequencer()

        # load new exposure time here (better: with XML parameter ?)
        self.set_exposure_time(exposuretime)
        self.primeheader["DATE-OBS"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # acquisition date

        self.reb.run_subroutine(name)

        time.sleep(exposuretime + waittime)

        # check for output image
        #getting tag from FPGA registers
        hextag = self.reb.fpga.get_time()
        imgname = os.path.join(self.rawimgdir,'0x%016x.img' % hextag)
        if os.path.isfile(imgname):
            self.get_headers()

            if name == "Bias":
                self.primeheader["SHUT_DEL"] = 0
            else:
                self.primeheader["SHUT_DEL"] = 100
            self.primeheader["IMGTYPE"] = name
            self.primeheader["EXPTIME"] = exposuretime
            self.save_to_fits(imgname, fitsname)
            self.imgtag = self.imgtag + 1
            hextag = generate_tag(self.imgtag)
            self.reb.fpga.set_time(hextag)  # setting up tag for next image

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.reb.fpga.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def save_to_fits(self, imgname, fitsname = ""):
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
        imgstr = os.path.splitext(os.path.basename(imgname))[0]
        self.primeheader["IMAGETAG"] = imgstr
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
            # exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
            exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
            self.get_extension_header(num, exthdu)
            hdulist.append(exthdu)

        # More header HDUs
        exthdu = pyfits.BinTableHDU(name="TEST_COND")
        self.testheader.update(self.monochromator.testheader)
        dict_to_fitshdu(self.testheader,exthdu)
        hdulist.append(exthdu)
        exthdu = pyfits.BinTableHDU(name="CCD_COND")
        dict_to_fitshdu(self.opheader,exthdu)
        hdulist.append(exthdu)

        # Sequencer dump
        exthdu = get_sequencer_hdu(self.reb.fpga)
        hdulist.append(exthdu)

        # Writing file
        if not fitsname:  # structure for specific tests
            fitsdir = os.path.join(self.fitstopdir,time.strftime('%Y%m%d',time.localtime()))
            if not os.path.isdir(fitsdir):
                os.mkdir(fitsdir)
            fitsname = os.path.join(fitsdir, imgstr +'.fits')
        # else: using LSST scheme for directory and image name, already built in fitsname

        primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
        primaryhdu.header["DATE"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # FITS file creation date
        hdulist.writeto(fitsname, clobber=True)

        print("Wrote FITS file "+fitsname)

def start():
    """
    Bench start-up operations strung together.

    :return: Bench()
    """
    b = Bench()
    b.REBpowerup()
    wait_for_action("REB can be connected to CCD now.")
    b.CCDpowerup()
    # Puts CCD in waiting state by clearing periodically, while waiting for a new command.
    b.waiting_sequence()
    return b


def stop(b):
    b.CCDshutdown()
    b.bench_shutdown()


def PTC(b):
    """
    Acquires a series of pairs of flat with increasing exposure times.
    Could also use Peter Doherty's ccdacq for this, would give structure for file names and directories.
    :param b:
    :return:
    """
    # TODO: power / set lamp or laser ?
    ptclog = open(os.path.join(self.fitstopdir,"PTClog.txt"), mode='a')
    for exptime in range(0.25, 5, 0.25):
        first = b.imgtag
        b.execute_sequence('Acquisition',exposuretime=exptime)
        second = b.imgtag
        b.execute_sequence('Acquisition',exposuretime=exptime)
        ptclog.write("%4.2f\t%s\t%s\n" % (exptime, first, second))
    ptclog.close()


def timing_ramp(b):
    """
    Series of acquisitions to compare timings.
    """
    # TODO: power on laser/other ?
    ramplog = open(os.path.join(self.fitstopdir,"ramplog.txt"), mode='a')
    func1 = 2
    slice1 = 6  # TBC depending on which slice and which function we test
    for imtype in ['Bias','Acquisition']:
        for duration in range(150,450,20):
            curfunc = b.reb.fpga.dump_function(func1)
            curfunc.timelengths[slice1] = duration
            b.reb.fpga.send_function(func1, curfunc)
            ramplog.write("%d\t%s\n" % (duration, b.imgtag))
            b.execute_sequence(imtype)
    ramplog.close()
    

if __name__ == '__main__':
    b = start()
    PTC(b)

