#! /usr/bin/env python
#
# LSST / LPNHE
#
# Testing WREB with CABAC2

__author__ = 'juramy'

import lsst.camera.generic.reb as reb
import time
import os
import logging
import fpga
import astropy.io.fits as pyfits


class WREB(reb.REB):
    useCABACbias = True
    xmldir = "/home/lsst/lsst/py/camera/wreb/"
    exposure_unit = 0.026  # duration of the elementary exposure subroutine in s
    min_exposure = int(0.1 / exposure_unit)  # minimal shutter opening time (not used for darks)

    def __init__(self, rriaddress = 2, ctrl_host = None, stripe_id=[0]):
        reb.REB.__init__(self, rriaddress, ctrl_host, stripe_id)
        self.fpga = fpga.FPGA1(ctrl_host, rriaddress)
        self.fpga.n_sensors_boardtemp = 6  # fewer board temperature sensors than on a full REB
        # self.fpga.supplies = ['DREB', 'CLK_H', 'DPHI', 'HTR', 'ANA', 'OD']
        # currently power supplies readback has been removed from the board
        self.fpga.supplies = []
        self.fpga.stop_clock()  # stops the clocks to use as image tag
        self.fpga.write(0x400006, 0)  # pattern generator off
        self.config = {"VSUB": 0}  # depends on power supply values and board configuration
        self.xmlfile = "sequencer-wreb.xml"
        # load 0 on default state to prep for REB start-up
        self.fpga.send_function(0, fpga.Function(name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

     # --------------------------------------------------------------------

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionary and writes to CABAC, then checks the readback.
        Note: if params is empty, this simply rewrites the same parameters in the CABAC objects and updates config.
        THERE IS NO SAFETY CHECK on this function, use set_biases as a high-level function for biases.
        """
        for s in self.stripes:
            for param in iter(params):
                print("Setting %s to %r" % (param, params[param]))
                self.fpga.set_cabac_value(param, params[param], s)
        time.sleep(0.1)

        self.config.update(params)  # for higher level parameters not in cabac
        for s in self.stripes:
            self.config.update(self.fpga.get_cabac_config(s), check=True)

    def get_cabac_config(self):
        """
        Read CABAC configurations and store it to config.
        Useful for recovery and headers.
        """
        cabacconfig = {}
        for s in self.stripes:
            cabacconfig.update(self.fpga.get_cabac_config(s), check=False)

        self.config.update(cabacconfig)

        return cabacconfig

    def cabac_reset(self):
        """
        Resets all CABACs.
        This should not be done just because you thought it was a good idea at the time.
        :return:
        """
        for s in self.stripes:
            self.fpga.reset_cabac(s)
        self.get_cabac_config()  # updates CABAC fields

    def send_aspic_config(self, params):
        """
        Sets ASPIC parameters, writes to ASPIC, then check readback.
        Notes: if params is empty, this simply rewrites the same parameters in the ASPIC objects and updates config.
        """
        for s in self.stripes:
            for param in iter(params):
                self.fpga.set_aspic_value(param, params[param], s)
            time.sleep(0.1)
            self.config.update(self.fpga.get_aspic_config(s, check=True))

    def config_aspic(self):
        settings = {"GAIN": 0b1000, "RC": 0b11, "AF1": False, "TM": False, "CLS": 0}
        self.send_aspic_config(settings)

    def check_bias_safety(self, param, value):
        """
        Checks that the given parameter is safe for the CCD, comparing to saved values.
        :param param: string
        :param value: float
        :return: bool
        """
        # safety: OG<OD
        if param == "OG":
            if "OD" in self.config:
                if self.config["OD"] < value:
                    print("Warning: trying to program OG at %f, higher than OD" % value)
                    return False
                else:
                    return True
            else:
                print("No saved value of OD to compare to OG")
                return False
        # safety: OD-RD < 20 V, but preferably also OD>RD
        elif param in ['OD', 'RD']:
            if param == "OD":
                od = value
                if "RD" in self.config:
                    rd = self.config["RD"]
                else:
                    print("No saved value of RD to compare to OD")
                    return False
            elif param == "RD":
                rd = value
                if "OD" in self.config:
                    od = self.config["OD"]
                else:
                    print("No saved value of OD to compare to RD")
                    return False
            if od < rd:
                print("Warning: trying to program OD lower than RD")
                return False
            elif od > rd+20:
                print("Warning: trying to program OD higher than RD + 20 V")
                return False
            else:
                return True
        else:
            return True

    def validate_biases(self, params):
        """
        Intermediate step to manage safe changes in bias values, from CABAC or alternative biases.
        :param params: dict
        :return:
        """
        valid = {}

        if self.useCABACbias:
            # by steps
            for param in params:
                if self.check_bias_safety(param, params[param]):
                    valid[param] = params[param]
                else:
                    # try half-way
                    half = params[param]/2
                    if self.check_bias_safety(param, half):
                        valid[param] = half
            self.send_cabac_config(valid)

        else:
            # simultaneous activation works fine if all new values are valid
            configsave = self.config
            self.config.update(params)
            valid = params.copy()
            for param in params:
                if not self.check_bias_safety(param, params[param]):
                    # cancels change
                    valid = {}
                    self.config.update(configsave)
                    break
            self.fpga.set_bias_voltages(valid)
        return valid

    def set_biases(self, params):
        """
        Manages safe changes in bias values, from CABAC or alternative biases.
        :param params: dict
        :return:
        """
        target = params.copy()
        for i in range(len(params)):
            valid = self.validate_biases(target)
            if valid == target:
                break  # all done
            elif not valid:
                print("No valid biases to be set")
                break
            else:
                # repeat loop for the rest
                for param in valid:
                    target.pop(param)

    def set_parameter(self, param, value, stripe = 0, location = 3):
        """
        Generic interface to set any single parameter of the REB, and check the readback if possible.
        :param param:
        :param value:
        :return:
        """
        if param in self.fpga.aspic_top[0].params:
            self.fpga.set_aspic_value(param, value, stripe, location)
            time.sleep(0.1)
            self.config.update(self.fpga.get_aspic_config(stripe, check=True))

        elif param in self.fpga.cabac_top[0].params:
            if self.check_bias_safety(param, value):
                self.fpga.set_cabac_value(param, value, stripe, location)
                time.sleep(0.1)
                self.config.update(self.fpga.get_cabac_config(stripe, check=True))

        elif param in ["SL", "SU", "RGL", "RGU", "PL", "PU"]:
            self.fpga.set_clock_voltages({param: value})
            self.config.update({param: value})

        elif param == "I_OS":
            self.fpga.set_current_source({param: value}, stripe)
            self.config.update({param: value})

        else:
            print("Warning: unidentified parameter for the REB: %s" % param)

    # --------------------------------------------------------------------

    def REBpowerup(self):
        """
        To be executed at power-up to safeguard CABAC2.
        :return:
        """
        # power-up the CABAC low voltages, Vsub and VddOD if using CABAC biases
        self.fpga.cabac_power(True, useCABACbias=self.useCABACbias)
        # power-up the clock rails (in V)
        print("Power on clock rails supplies here")
        time.sleep(2)
        rails = {"SL": 0.5, "SU": 9.5, "RGL": 0, "RGU": 10, "PL": 0, "PU": 9.0}
        self.fpga.set_clock_voltages(rails)
        self.config.update(rails)

        # put all CABAC biases at board GND (must know Vsub), including spare
        Vsuboffset = - self.config["VSUB"]
        self.send_cabac_config({"OD": Vsuboffset, "GD": Vsuboffset, "RD": Vsuboffset})
        # staged for CCD safety
        self.send_cabac_config({"OG": Vsuboffset, "SPA": Vsuboffset})

    def CCDpowerup(self):
        """
        Sequence to power up the CCD.
        """

        #starting drain voltages
        drains = {"RD": 8, "OD": 12, "GD": 10}
        self.set_biases(drains)

        time.sleep(0.5)

        #starting OG voltage
        og = {"OG": 3.5}
        self.set_biases(og)

        time.sleep(0.5)

        #sets clock currents on CABAC
        iclock = {"IC": 200}
        self.send_cabac_config(iclock)
        #time.sleep(1)

        #puts current on CS gate
        dacOS = {"I_OS": 0xfff}
        for s in self.stripes:
            self.fpga.set_current_source(dacOS, s)
        self.config.update(dacOS)

        #load sequencer if not done, else rewrite default state of sequencer (to avoid reloading all functions)
        if self.seq:
            self.fpga.send_function(0, self.seq.get_function(0))
        else:
            self.load_sequencer()

        self.fpga.enable_bss(True)
        print('BSS can be powered on now.')

    def CCDshutdown(self):
        """
        Sequence to shutdown power to the CCD.
        """
        print('BSS must be shutdown at this time.')
        time.sleep(5)
        self.fpga.enable_bss(False)

        #sets the default sequencer clock states to 0
        self.fpga.send_function(0, fpga.Function(name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

        #shuts current on CS gate
        dacOS = {"I_OS": 0}
        for s in self.stripes:
            self.fpga.set_current_source(dacOS, s)
        self.config.update(dacOS)

        #shuts clock currents on CABAC
        iclock = {"IC": 0}
        self.send_cabac_config(iclock)

        time.sleep(0.1)

        # shuts OG voltage
        og = {"OG": 0}
        self.set_biases(og)

        time.sleep(0.5)

        #shutting drain voltages
        drains = {"OD": 0, "GD": 0, "RD": 0}
        self.set_biases(drains)

        time.sleep(0.5)
        print('CCD shutdown complete on WREB.')

    def REBshutdown(self):
        """
        To be executed when shutting down the WREB to safeguard CABAC1.
        :return:
        """
        # clock rails first (in V)
        rails = {"SL": 0, "SU": 0, "RGL": 0, "RGU": 0, "PL": 0, "PU": 0}
        self.fpga.set_clock_voltages(rails)
        self.config.update(rails)
        # shutdown the CABAC low voltages
        self.fpga.cabac_power(False, useCABACbias=self.useCABACbias)
        # need to shutdown VddOD right here on power supply if not using CABAC biases (else it's done above)
        #sets the default sequencer clock states to 0
        self.fpga.send_function(0, fpga.Function(name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

    # --------------------------------------------------------------------


def save_to_fits(R, channels=None, rawimg='', fitsname = ""):  # not meant to be part of REB class, will call other instruments
    """
    Managing FITS creation from img file and adding other header information.
    :param R: WREB
    :param channels: list of channels
    :param fitsname: name if not using default structure.
    :return:
    """
    if rawimg:
        imgname = rawimg
    else:
        imgname = R.make_img_name()
    if os.path.isfile(imgname):
        hdulist = R.conv_to_fits(imgname, channels, displayborders=False)
        primaryhdu = hdulist[0]
        imgstr = os.path.splitext(os.path.basename(imgname))[0]
        primaryhdu.header["IMAGETAG"] = imgstr
        if not fitsname:
            fitsname = R.make_fits_name(imgstr)
        # else: using LSST scheme for directory and image name, already built in fitsname
        primaryhdu.header["FILENAME"] = os.path.basename(fitsname)
        primaryhdu.header["DATE-OBS"] = R.tstamp
        primaryhdu.header["TESTTYPE"] = 'WREB test'
        primaryhdu.header["IMGTYPE"] = R.seqname
        localheader = pyfits.Header.fromtextfile("localheader.txt")
        primaryhdu.header.update(localheader)
        # for more meta, use the driver
        # Extended header HDU for REB operating conditions (no readback here, get it from the config dictionary).
        exthdu = pyfits.ImageHDU(name="CCD_COND")
        for keyword in R.config:
            exthdu.header[keyword] = R.config[keyword]
        hdulist.append(exthdu)

        # Sequencer content (no actual readback, get it from the seq object)
        seqhdu = pyfits.TableHDU.from_columns([pyfits.Column(format='A73',
                                                         array=reb.get_sequencer_string(R.seq),
                                                         ascii=True)])
        seqhdu.header['EXTNAME'] = 'SEQUENCER'
        hdulist.append(seqhdu)

        hdulist.writeto(fitsname, clobber=True)

        print("Wrote FITS file "+fitsname)
    else:
        print("Did not find the expected raw file: %s " % imgname)

if __name__ == "__main__":

    logfile = os.path.join('/home/lsst/logs', time.strftime('wreb-log-%Y%m%d.txt', time.gmtime()))
    logging.basicConfig(filename = logfile,
                        level = logging.DEBUG,
                        format = '%(asctime)s: %(message)s')
    R = WREB(rriaddress=0xFF, stripe_id=[0])

    # here power on power supplies
    R.REBpowerup()
    time.sleep(0.1)
    R.CCDpowerup()
    R.config_aspic()
    #R.load_sequencer(R.xmlfile)
    #R.config_sequence("Bias")
    #R.execute_sequence()
    #save_to_fits(R)
    #R.f.set_cabac_value("MUX", ("P0", "P1"), 0, 2)  # to check these clocks on top CABAC of stripe 0
    #R.f.set_cabac_value("OFMUX", 140, 0, 2)  # required offset to the clock mux
    # TO BE CHECKED: only one of each mux outputs should be active at any time over all CABACs ?!?!
