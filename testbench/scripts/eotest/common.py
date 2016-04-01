# Operations common to various EO tests
import os.path

from lsst.testbench.bench import Bench

#B = Bench()

#import lsst.testbench.scripts.ccd.functions


def CCDready(self):
    """
    Checks that the CCD is ready, and powers it up if it is not.
    :param self:
    :return:
    """
    biases = self.reb.get_cabac_config()
    CCDon = True
    for bias in ['OD', 'GD', 'RD']:
        if biases[bias] < 10:
            CCDon = False

    if not CCDon:
        self.powerup_CCD()
    # for cases with CCD on but not BSS
    elif not self.bss.voltageStatus():
        self.setup_BSS()
        self.bss.enable(delay=20.0)

Bench.CCDready = CCDready


def set_ccdID(self, manu, manutype, sernum):
    self.reb.set_sensorID(self, manu, manutype, sernum)

Bench.set_ccdID = set_ccdID

def make_eo_directory(self, testtype):
    # should take CCD info from self.reb
    pass

def make_eo_filename(self, testtype, imgtype):
    #TODO: see in TS code, take from stored values in B.reb
    pass

def acquire_eotest(self, expname, exptime, fitsname):
    """
    Runs the CCD, acquire and save image. fitsname should include the directory if not using default.
    :param self:
    :return:
    """
    m = self.execute_reb_sequence(name=expname, exptime=exptime, delaytime=4, withclap=False, withmeta=True)

    i = self.conv_to_fits(channels=validamps)
    self.save_to_fits(i, m, fitsname=os.path.join(eodir, fitsname), LSSTstyle=True)

Bench.acquire_eotest = acquire_eotest
