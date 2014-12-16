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
import lsst.camera.reb as reb
import numpy as np
import pyfits

stand_alone = True

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
    today = time.gmtime()
    tagstr = time.strftime('%Y%m%d', today)+'%05d' % number
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
        seq = fpga.dump_function(ifunc)
        for islice in range(16):
            i = ifunc * 16 + islice
            slicenum[i] = hex(i)[2:]
            output[i] = bin(seq.outputs[islice])[2:]
            duration[i] = seq.timelengths[islice]

    for i, addr in enumerate(sorted(progaddr)):
        slicenum[i+256] = '30' + hex(addr)[2:]
        output[i+256] = prog.instructions[addr].__repr__()[:20]
        duration[i+256] = prog.instructions[addr].repeat

    slicecol = pyfits.Column(name="Address", format='A4', array=slicenum)
    outputcol = pyfits.Column(name="Output", format='A32', array=output)
    durationcol = pyfits.Column(name="Time", format='I8', array=duration)

    exthdu = pyfits.new_table([slicecol, outputcol, durationcol], tbtype='TableHDU')
    # add name to extension here
    exthdu.header["EXTNAME"] = "SEQ_CFG"

    return exthdu


def check_xmlrpc(server, idstr):
    """

    :param server: xmlrpclib.ServerProxy
    :param idstr:
    """
    try:
        checkstr = server.checkConnection()
    except:
        checkstr = server.getModel()
    if checkstr != idstr:
        errorstr = "Incorrect connection: returns %s, expect %s " % (checkstr, idstr)
        if stand_alone:
            print(errorstr)
        else:
            raise ValueError(errorstr)


class TempController():
    """
    Managing Lakeshore temperature controller.
    """
    temp_target = -100
    rampPID = (35,0,0)
    temp = -100

    def __init__(self, logger=None):  # TODO
        #self.server = xmlrpclib.ServerProxy("http://lpnlsst:/")
        #connect
        #check
        self.logger = logger

    def setTemp(self, temp):
        """

        :param temp: float
        """
        self.temp = temp

    def getTemp(self):
        # to be changed when XMLRPC is available
        return self.temp

    def setPID(self, p, i, d):
        pass

class BackSubstrate():
    """
    Managing back-substrate voltage controlled by Keithley 6487
    """
    setvoltbss = 0  # desired voltage setting (independent of actual value)
    count = 1  # number of measures for monitoring
    rate = 1.0  # monitoring rate
    name = "Keithley 6487"

    def __init__(self):
        self.server = xmlrpclib.ServerProxy("http://lpnlsst:8088/")
        self.server.connect()
        check_xmlrpc(self.server, "6487" )

    def config(self, voltage=0):
        """
        Configuration of voltage, current limits and current readout.
        """

        if abs(voltage) < 50:
            range = 1
        else:
            range = 2  # 500 V
        self.server.setVoltageRange(range)

        self.set_volt(voltage)
        #self.selectCurrent(2e-5)  # selecting current range: not implemented yet
        self.server.zeroCorrect()
        self.server.setCurrentLimit(0)  # 25 uA
        self.server.setRate(self.rate)

    def check_config(self):
        inti = self.server.getCurrentLimit()
        if inti != 0:
            raise IOError("Wrong current limit setting on bss: %d" % inti)
        # can add check on range (getVoltageRange) and setvoltbss (getVoltage)

    def set_volt(self, voltage):
        """
        Changes voltage without changing configuration
        """
        if voltage < 0:
            self.server.setVoltage(float(voltage))
            self.setvoltbss = voltage
        else:
            errorstr = "Asked for a positive back-substrate voltage (%f), not doing it. " % voltage
            if stand_alone:
                print(errorstr)
            else:
                raise ValueError(errorstr)

    def enable(self):

        self.server.sourceVoltage(1)

        time.sleep(30)

        #check
        ena = self.server.voltageStatus()
        if ena != 1:
            raise IOError("Error on back-substrate voltage: not enabled.")

    def disable(self):

        self.server.sourceVoltage(0)
        time.sleep(10)
        while self.server.voltageStatus() != 0:
            time.sleep(1)

    def get_current(self):
        """
        Get a single current reading.
        :return: double
        """
        self.count = 1
        self.server.startSequence(1)
        while self.server.status() == 3:  # TBC
            time.sleep(1)

        return self.server.getSequence()[0]

    def set_monitor_rate(self, rate):
        """
        Sets rate of monitoring to a new value.
        Useful to do before long exposures.
        :param rate:
        :return:
        """
        self.rate = rate
        self.server.setRate(self.rate)

    def start_monitor(self, exptime):
        """
        Configures back-substrate current monitoring for an exposure
        :param exptime: double
        """
        self.count = int(exptime * self.rate)+ 1
        self.server.startSequence(self.count)

    def read_monitor(self):
        """
        Reads the latest sequence from the monitoring photodiode. Averages the results after eliminating outliers.
        :return: double
        """
        while self.server.status() == 3:
            time.sleep(1)
        readarray = np.array(self.server.getSequence())
        av_read = readarray.mean()

        return av_read

    def get_operating_header(self):
        """
        Gets voltage and current on back substrate in header dictionary format.
        : return : dict
        """
        vss = "0.0"
        if self.server.voltageStatus():
            # vss = "{:.2f}".format(self.server.getVoltage())
            vss = "%.2f" % self.server.getVoltage()
        # otherwise back-substrate voltage is off
        if self.count > 1:
            imon = self.read_monitor()
        else :
            imon = self.get_current()
        iss = ":%.3E" % imon

        return {"V_BSS": vss, "I_BSS": iss}


class Source(object):
    """
    Management of the light sources and iron 55 source.
    """
    source_selector = ("Fe55", "XeHg", "QTH", "Laser")
    lamp_list = ["XeHg", "QTH"]
    XED_SHUTTER = 0  # activate Fe55 arm (when it will be motorized), name chosen for compatibility
    MONO_SHUTTER = 1  # deactivates Fe55, same
    rate = 1.0  # monitoring photodiode, spl/s
    QTH_power = 150.0
    XeHg_power = 200.0
    laser_current = 25.0
    laser_channel = 2

    def __init__(self, logger=None):
        self.source_name = None
        self.laser = xmlrpclib.ServerProxy("http://lpnlsst:8082/")
        self.ttl = xmlrpclib.ServerProxy("http://lpnlsst:8083/")
        self.ttl.connect()
        # check_xmlrpc(self.ttl, True)
        # light sources: create objects here, does not try to connect
        self.qth = xmlrpclib.ServerProxy("http://lpnlsst:8089/")
        self.xehg = xmlrpclib.ServerProxy("http://lpnlsst:8085/")
        self.multi = None
        self.logger = logger

    def setChannel(self, channel):
        """
        Activates or retracts Fe55 arm, when it exists
        """
        if channel == self.XED_SHUTTER:
            # activates
            pass
        else:
            # retracts
            pass

    def select_source(self, sourcetype, wl=635.0):
        """
        Selects source and configure it, does not power up (except Fe55).
        :param sourcetype: string
        :param wl: double
        :return:
        """
        if sourcetype not in self.source_selector:
            raise ValueError("Unknown type of source")
        self.source_name = sourcetype

        if sourcetype == "Fe55":
            self.setChannel(self.XED_SHUTTER)
            time.sleep(5)  # time to move (tbc)
        else:
            self.setChannel(self.MONO_SHUTTER)

        # monitoring photodiode
        try:
            self.multi = xmlrpclib.ServerProxy("http://lpnlsst:8087/")
            self.multi.connect()
            check_xmlrpc(self.multi, "6514")
            self.multi.zeroCorrect()
            self.multi.setRate(self.rate)  # default choice: 1 reading/s
        except:
            self.multi = None

        if sourcetype == "Laser":
            self.laser.connect()
            check_xmlrpc(self.laser, "THORLABS MCLS vers 1.06")
            # default current values give approximately 1.5 mW of power
            if wl<500:
                self.laser_channel = 1  # 406 nm
                self.laser_current = 26.0  # min: 23, max: 35
            elif wl<750:
                self.laser_channel = 2  # 635 nm
                self.laser_current = 50.0  # min: 45, max: 64
            elif wl<900:
                self.laser_channel = 3  # 808 nm
                self.laser_current = 26.0  # min: 20, max: 66
            else:
                self.laser_channel = 4  # 980 nm
                self.laser_current = 30.0  # min: 25, max: 55
            for channel in range(1,5):
                if channel == self.laser_channel:
                    self.laser.select(self.laser_channel)
                else:
                    self.laser.select(-channel)  # make sure to unselect others
            self.setWatts(self.laser_current)
        elif sourcetype == "QTH":
            self.ttl.selectQTH()
            self.qth.connect()
            check_xmlrpc(self.qth, "69931")
            self.setWatts(self.QTH_power)
        elif sourcetype == "XeHg":
            self.ttl.selectXeHg()
            self.xehg.connect()
            check_xmlrpc(self.xehg, "20")
            self.setWatts(self.XeHg_power)

        log(self.source_name, self.logger, "Selected")

    def getWatts(self):
        pw = 0
        if self.source_name == "Laser":
            pw = self.laser.getPower(self.laser_channel)*0.001  # converts to Watts
        elif self.source_name == "QTH":
            pw = self.qth.getPresetPower()
        elif self.source_name == "XeHg":
            pw = self.xehg.getPresetPower()
        return pw

    def setWatts(self, power):
        """
        Sets power for lamps (in W), current for laser (in mA)
        :param power: float
        """
        if self.source_name == "Laser":
            self.laser_current = float(power)
            self.laser.setCurrent(self.laser_channel, self.laser_current)
        elif self.source_name == "QTH":
            self.qth.setFluxControl(0)
            self.QTH_power = float(power)
            self.qth.setPresetPower(self.QTH_power)
        elif self.source_name == "XeHg":
            self.xehg.setFluxControl(0)
            self.XeHg_power = float(power)
            self.xehg.setPresetPower(self.XeHg_power)
        log(self.source_name, self.logger, "Set Watts", power)

    def getMonitor(self):
        """
        Gets a single instantaneous reading of the current in the monitoring photodiode.

        """
        if self.multi:
            self.multi.startSequence(1)
            while self.multi.status() == 3:
                time.sleep(1)
            reading = self.multi.getSequence()
            return reading[0]

        return 0

    def start_monitor(self, exptime):
        """
        Configures current monitoring for an exposure
        :param exptime: double
        """
        if self.multi:
            if exptime> 60 :
                self.rate = 10.0  # for long exposures, more stable
            else:
                self.rate = 1.0
            self.multi.setRate(self.rate)

            num = int(exptime/self.rate)+ 1
            self.multi.startSequence(num)

    def read_monitor(self):
        """
        Reads the latest sequence from the monitoring photodiode. Averages the results after eliminating outliers.
        :return: double
        """
        if self.multi:
            readarray = np.array(self.multi.getSequence())
            # TODO: need to correct the sequence we get currently
            av_read = readarray.mean()  # TODO: remove outliers (dark)
        else:
            av_read = 0

        return av_read

    def getAlim(self):
        """
        Current limit on lamps (target current for laser).
        """
        if self.source_name == "XeHg":
            return self.xehg.getPresetCurrent()
        elif self.source_name == "QTH":
            return self.qth.getPresetCurrent()
        elif self.source_name == "Laser":
            return self.laser.getCurrent(self.laser_channel)*0.001  # put in Amps
        return 0

    def on(self):
        if self.source_name in self.lamp_list:
            # to move the filter wheel to the home position:
            self.ttl.homeFilterWheel()
            while self.ttl.status()[2] != 0:
                time.sleep(1)

            self.ttl.openShutter()

        if self.source_name == "XeHg":
            self.xehg.power(1)
            time.sleep(20)
            self.xehg.setFluxControl(1)
        elif self.source_name == "QTH":
            self.qth.power(1)
            time.sleep(20)
            self.qth.setFluxControl(1)
        elif self.source_name == "Laser":
            self.laser.enable()

        log(self.source_name, self.logger, "On")

    def off(self):
        if self.source_name in self.lamp_list:
            ret = self.ttl.closeShutter()
            #if ret != 0:
            #    raise IOError("Error on shutter close")

        if self.source_name == "XeHg":
            self.xehg.setFluxControl(0)
            self.xehg.power(0)
        elif self.source_name == "QTH":
            self.qth.setFluxControl(0)
            self.qth.power(0)
        elif self.source_name == "Laser":
            self.laser.disable()

        log(self.source_name, self.logger, "Off")


class Monochromator(object):
    """
    Management of monochromator and input filter
    """
    testheader = {"MONOTYPE":"Triax", "MONOMODL":"180"}
    slitsize = 30
    grating = 0
    name = "Triax 180"

    def __init__(self, logger=None):
        self.triax = xmlrpclib.ServerProxy("http://lpnlsst:8086/")
        # TODO: add filter management (when there will be filters)
        self.logger = logger

    def connect(self):
        self.triax.connect()
        check_xmlrpc(self.triax, "1")

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

    def setWavelength(self, wavelength, SelectGrating=False):
        """
        Moves the monochromator to the selected wavelength and waits until it is done.
        Calculates automatically which grating to use if authorized to change.
        """

        if SelectGrating:
            if wavelength < 800:
                self.grating = 0
                lines = 1198
            elif wavelength < 1400:
                self.grating = 1
                lines = 1198
            else:
                self.grating = 2
                lines = 599
            self.setGrating(self.grating)
            self.testheader["MONOPOS"] = self.grating
            self.testheader["MONOGRAT"] = lines

        wl = float(wavelength)
        self.triax.setWavelength(wl)
        while self.triax.status() == 0:
            time.sleep(1.0)
        # check
        new_wl = self.getWavelength()
        if abs(wl-new_wl) > 1:
            # try again
            self.triax.setWavelength(wl)
            time.sleep(1.0)
            new_wl = self.getWavelength()  # will wait
            if abs(wl-new_wl) > 1:
                errorstr = "Monochromator cannot reach wavelength %f" % wl
                if stand_alone:
                    print(errorstr)
                else:
                    raise ValueError(errorstr)

        log(self.triax.name, "Wavelength", wl)

    def getWavelength(self):
        """
        Reads the wavelength once movement is stopped.
        """
        while self.triax.status() == 0:
            time.sleep(1.0)
        return self.triax.getWavelength()

    def setFilter(self, value):
        pass

    def setGrating(self, value):
        self.grating = int(value)
        if self.grating in [0,1,2]:
            self.triax.setGrating(self.grating)
            log(self.triax.name, "Grating", self.grating)
        else:
            errorstr = "Non-existent grating value %d" % value
            if stand_alone:
                print(errorstr)
            else:
                raise ValueError(errorstr)


class Bench(object):
    """
    Internal representation of the full bench
    """
    opheader = {}
    testheader = {}
    primeheader = {}
    reb_id = 2
    strip_id = 0
    nchannels = 16
    imgtag = 0
    xmlfile = "camera/reb/sequencer-soi.xml"
    rawimgdir = "/home/lsst/test_images"
    fitstopdir = "/home/lsst/test_frames"
    logger = None  # update later if using logger
    # The following should come from the XML file instead
    imglines = 2020
    imgcols = 550
    exposuresub = "Exposure"
    darksub = "DarkExposure"
    exposure_unit = 0.020  # duration of the elementary exposure subroutine in s
    min_exposure = 0.1/exposure_unit  # minimal duration of an exposure to avoid blocking shutter (not used for darks)
    testtype = "Test"

    def __init__(self, logger=None):
        self.reb = reb.REB(reb_id=self.reb_id)
        self.seq = reb.fromxmlfile(self.xmlfile)
        self.primeheader["CTRLCFG"] = self.xmlfile
        self.bss = BackSubstrate()  # logged in higher-level class k6487
        self.temp = TempController(logger)
        self.lamp = Source(logger)
        self.monochromator = Monochromator(logger)

    def REBpowerup(self):
        """
        Operations after powering the REB (through CCS)
        :return:
        """
        try:
            self.reb.read(0, 5)
        except:
            wait_for_action("Could not establish communication with DREB, try rebooting RCE.")
            self.reb.read(0, 5)

        self.reb.set_strip(self.strip_id)
        self.reb.cabac_reset()
        self.reb.send_sequencer(self.seq)
        hextag = generate_tag(self.imgtag)
        self.reb.set_time(hextag)  # using time registers to store image tag (do not run clock in this case)
        #self.CCDshutdown()

        print("REB ready to connect to CCD")
        #subprocess.Popen("imageClient %d" % self.reb_id, shell=True)  # hijacks the ipython shell
        print("Remember to launch imageClient in %s" % self.rawimgdir)

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """

        #sets the default sequencer clock states to 0
        self.reb.send_function(0, reb.Function( name="default state",
                                                timelengths={0: 2, 1: 0},
                                                outputs={0: 0, 1: 0} ))

        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.reb.send_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG": 3.5}
        self.reb.send_cabac_config(og)

        time.sleep(1)

        #sets clock rails
        dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
        self.reb.set_dacs(dacs)

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.reb.send_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS": 0xfff}
        self.reb.set_dacs(dacOS)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.reb.send_function(0, reb.Function( name="default state",
                                            timelengths={0: 2, 1: 0},
                                            outputs={0: 0x6bc, 1: 0} ))

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
        self.reb.send_function(0, reb.Function( name="default state",
                                                timelengths={0: 2, 1: 0},
                                                outputs={0: 0, 1: 0} ))
        #currents on CABAC clocks to 0
        self.reb.send_cabac_config({"IC": 0})
        #clock rails to 0
        self.reb.set_dacs({"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0})

        time.sleep(1)

        #currents on OG to 0
        self.reb.send_cabac_config({"OG": 0})

        time.sleep(1)

        #drains to 0
        self.reb.send_cabac_config({"OD": 0, "GD": 0, "RD": 0})

        print("CCD shutdown complete")

    def bench_shutdown(self):
        pass
        #self.lamp.ttl.closeShutter()

    def update_tag(self, num = 1):
        """
        Updates the clock tag to current date and given sequence number
        :param num: int
        :return:
        """
        self.imgtag = num
        hextag = generate_tag(self.imgtag)
        self.reb.set_time(hextag)

    def select_source(self, sourcetype, wavelength=500.0):
        """
            Connects and starts whichever light source is going to be used
            """
        self.lamp.select_source(sourcetype, wavelength)
        self.testheader["SRCTYPE"] = sourcetype.upper()
        #self.testheader["SCRMODL"]  # source model
        self.testheader["SRCPWR"] = self.lamp.getWatts()

        if sourcetype in self.lamp.lamp_list:
            self.monochromator.connect()
            self.monochromator.setWavelength(wavelength, True)
            self.monochromator.set_slit_size(30)

    def get_headers(self):
        """
        Fills image header dictionaries for current setup.
        """
        #CCD operating conditions header
        self.opheader = self.reb.get_operating_header()

        self.opheader.update(self.bss.get_operating_header())
        # TODO: power supply currents and voltages

        #need to add instruments header, optional sequencer header
        self.primeheader["WIDTH"] = self.imgcols
        self.primeheader["HEIGHT"] = self.imglines
        self.primeheader["DETSIZE"] = '[0:%d,0:%d]' % (self.imgcols*self.nchannels/2, 2*self.imglines)
        self.primeheader["TESTTYPE"] = self.testtype
        try:
            wavelength = self.monochromator.getWavelength()
        except:
            wavelength = 0.0
        self.primeheader["MONOWL"] = wavelength

        self.monochromator.testheader["MONOWL"] = wavelength
        self.primeheader["CCDTEMP"] = self.temp.getTemp()

    def get_extension_header(self, REBchannel, fitshdu, borders = False):
        """
        Builds FITS extension header with position information for each channel
        :param REBchannel: int
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
            parstringlow = '1:%d' % self.imglines
            parstringhigh = '%d:%d' % (2*self.imglines, self.imglines+1)
            colwidth = self.imgcols
            extheader['DETSIZE'] = self.primeheader["DETSIZE"]
            extheader['DATASEC'] = '[1:%d,1:%d]' % (self.imgcols, self.imglines)

        if REBchannel<self.nchannels/2:
            pdet = parstringlow
            si = colwidth*(REBchannel+1)
            sf = colwidth*REBchannel+1
        else :
            pdet = parstringhigh
            # previous geometry
            #si = colwidth*(self.nchannels-1-REBchannel)+1
            #sf = colwidth*(self.nchannels-REBchannel)
            si = colwidth*(REBchannel-self.nchannels/2)+1
            sf = colwidth*(REBchannel-self.nchannels/2+1)

        extheader['DETSEC'] = '[%d:%d,%s]' % (si,sf,pdet)

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

    def get_exposure_time(self, darktime=False):
        """
        Gets the exposure time from the subroutines in memory.
        (input in seconds). If darktime is set to true, gives the dark 'exposure' time instead.
        :param darktime: boolean
        """

        # look up address of exposure subroutine
        # then get current instruction
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            instruction = self.seq.program.instructions[darkadd]
        else:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            instruction = self.seq.program.instructions[exposureadd]
        iter = instruction.repeat

        return float(iter)*self.exposure_unit  # in seconds


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
        newiter = int(exptime/ self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        if lighttime:
            exposureadd = self.seq.program.subroutines[self.exposuresub]
            newinstruction = self.seq.program.instructions[exposureadd]
            newinstruction.repeat = max(newiter, self.min_exposure)  # This does rewrite the seq.program too
            self.reb.fpga.send_program_instruction(exposureadd, newinstruction)
        #same for dark subroutine
        if darktime:
            darkadd = self.seq.program.subroutines[self.darksub]
            newinstruction = self.seq.program.instructions[darkadd]
            newinstruction.repeat = max(newiter, 1)  # must not be 0 or sequencer gets stuck
            self.reb.fpga.send_program_instruction(darkadd, newinstruction)

    def execute_sequence(self, name, exposuretime=None, waittime=20, fitsname=""):
        """
        Executing a 'main' sequence from the XML file or a subroutine, when sequencer is ready
        :param self:
        :param name: string

        """

        # Wait until sequencer is finished with current sequence
        self.wait_end_sequencer()

        # load new exposure time here (better: with XML parameter ?)
        if exposuretime:
            self.set_exposure_time(exposuretime)
            exptime = exposuretime
        # else use preset exposure time
        else:
            darktime = (name == "Dark")
            exptime = self.get_exposure_time(darktime)

        self.primeheader["DATE-OBS"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # acquisition date

        self.reb.run_subroutine(name)

        self.bss.start_monitor(exptime+4)  # time for clearing before exposure
        self.lamp.start_monitor(exptime+4)
        time.sleep(exptime + waittime)
        self.primeheader["MONDIODE"] = self.lamp.read_monitor()

        # check for output image
        #getting tag from FPGA registers
        hextag = self.reb.get_time()
        imgname = os.path.join(self.rawimgdir,'0x%016x.img' % hextag)
        if os.path.isfile(imgname):
            self.get_headers()

            if name == "Bias":
                self.primeheader["SHUT_DEL"] = 0
            else:
                self.primeheader["SHUT_DEL"] = 100
            self.primeheader["IMGTYPE"] = name
            self.primeheader["EXPTIME"] = exptime
            self.save_to_fits(imgname, fitsname)
            # setting up tag for next image
            self.update_tag(self.imgtag + 1)

    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.reb.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def make_fits_name(self, imgstr):
        fitsdir = os.path.join(self.fitstopdir,time.strftime('%Y%m%d',time.gmtime()))
        if not os.path.isdir(fitsdir):
            os.mkdir(fitsdir)
        fitsname = os.path.join(fitsdir, imgstr +'.fits')
        return fitsname

    def save_to_fits(self, imgname, fitsname = ""):
        """
        Turns img file from imageClient into FITS file.
        """
        # Reading raw file to array
        dt = np.dtype('i4')
        buff = np.fromfile(imgname, dtype=dt)
        # negative numbers still need to be translated
        #buffer = np.vectorize(lambda i: i - 0x40000 if i & (1 << 17) else i )(buff)
        # also invert sign on all data
        #buffer = np.vectorize(lambda i: 0x3FFFF-i if i & (1 << 17) else -i-1 )(buff)
        # also make all values positive (to be tested)
        # 0 -> 1FFFF, 1FFFF -> 0, 20000 -> 3FFFF, 3FFFF -> 20000
        buffer = np.vectorize(lambda i: 0x5FFFF-i if i & (1 << 17) else 0x1FFFF-i)(buff)
        # reshape by channel
        length = self.imglines * self.imgcols
        buffer = buffer.reshape(length, self.nchannels)

        # Creating FITS HDUs:
        # Create empty primary HDU and fills header
        primaryhdu = pyfits.PrimaryHDU()
        imgstr = os.path.splitext(os.path.basename(imgname))[0]
        self.primeheader["IMAGETAG"] = imgstr
        dict_to_fitshdu(self.primeheader, primaryhdu)
        # also need info from 'localheader.txt'
        localheader = pyfits.Header.fromtextfile("camera/localheader.txt")
        primaryhdu.header.update(localheader)
        # Create HDU list
        hdulist = pyfits.HDUList([primaryhdu])

        # Add extension for channels HDUs
        for num in range(self.nchannels):
            chan = buffer[0:length,num]
            chan = chan.reshape(self.imglines, self.imgcols)
            y = chan.astype(np.int32)
            # create extension to fits file for each channel
            exthdu = pyfits.ImageHDU(data=y, name="CHAN_%d" % num)  # for non-compressed image
            # exthdu = pyfits.CompImageHDU(data=y, name="CHAN_%d" % num, compression_type='RICE_1')
            self.get_extension_header(num, exthdu)
            avchan = np.mean(y[11:522,1:2002])
            exthdu["AVERAGE"] = avchan
            hdulist.append(exthdu)

        # More header HDUs
        exthdu = pyfits.ImageHDU(name="TEST_COND")
        self.testheader.update(self.monochromator.testheader)
        dict_to_fitshdu(self.testheader, exthdu)
        hdulist.append(exthdu)
        exthdu = pyfits.ImageHDU(name="CCD_COND")
        dict_to_fitshdu(self.opheader,exthdu)
        hdulist.append(exthdu)

        # Sequencer dump
        exthdu = get_sequencer_hdu(self.reb.fpga)
        hdulist.append(exthdu)

        # Writing file
        if not fitsname:  # structure for specific tests
            fitsname = self.make_fits_name(imgstr)
        # else: using LSST scheme for directory and image name, already built in fitsname

        primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
        primaryhdu.header["DATE"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())  # FITS file creation date
        hdulist.writeto(fitsname, clobber=True)

        print("Wrote FITS file "+fitsname)

def start():
    """
    Bench start-up operations strung together.

    :return: Bench
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
    :param b: Bench
    :return:
    """
    b.select_source("Laser", 635)
    b.lamp.on()
    b.testtype = "PTC"
    ptclog = open(os.path.join(b.fitstopdir,"PTClog.txt"), mode='a')
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
    :param b: Bench
    """
    b.select_source("Laser", 635)

    ramplog = open(os.path.join(b.fitstopdir,"ramplog.txt"), mode='a')
    func1 = 2
    slice1 = 6  # TBC depending on which slice and which function we test

    for imtype in ['Bias','Acquisition']:
        if imtype == 'Acquisition':
            b.lamp.on()
            time.sleep(10)
        for duration in range(150,450,20):
            curfunc = b.reb.dump_function(func1)
            curfunc.timelengths[slice1] = duration
            b.reb.send_function(func1, curfunc)
            ramplog.write("%d\t%s\n" % (duration, b.imgtag))
            b.execute_sequence(imtype)
    ramplog.close()
    b.lamp.off()


def scan_pixel(b):
    """
    Acquiring an image with ADC sampling scanning the pixel readouts.
    :param b: Bench
    """
    # new dimensions for the fits files
    savecols = b.imgcols
    savelines = b.imglines
    b.imgcols = 256
    b.imglines = (savecols*savelines)/(b.imgcols+1)

    b.select_source("Laser", 635)
    b.lamp.on()
    b.reb.fpga.increment()
    hextag = generate_tag(b.imgtag)
    fitsname = b.make_fits_name('scan_%d.fits' % hextag)
    b.primeheader["IMGTYPE"] = "SCAN"
    b.execute_sequence('Acquisition', exposuretime=0.5, fitsname=fitsname)
    b.reb.fpga.stop_increment()
    #del b.primeheader["IMGTYPE"]

if __name__ == '__main__':
    # needed as long as not implemented in XMLRPC
    #b.temp.setTemp(-100)
    b = start()
    PTC(b)

