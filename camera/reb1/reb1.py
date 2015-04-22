#
# LSST / LPNHE
# Author: Claire Juramy from original by Laurent Le Guillou
#
"""
Testbench driver for REB (through direct calls to rriClient)
"""
import py.camera.generic.reb as reb
import py.camera.generic.rebxml as rebxml
import fpga0
import time
import string
import os

# =======================================================================

class REB(reb.REB):

    # ===================================================================

    def __init__(self, reb_id = 2,  ctrl_host = None, stripe_id = [0]):
        reb.REB.__init__(reb_id, ctrl_host, stripe_id)
        self.fpga = fpga0.FPGA0(ctrl_host, reb_id)
        self.full18bits = True
        self.set_stripes(stripe_id)  # stripe in use
        self.recover_filetag()  # in case we are recovering from software reboot and not hardware reboot

    # --------------------------------------------------------------------

    def set_stripes(self, liststripes):
        self.stripes = []
        bitval = 0
        for s in liststripes:
            if self.f.check_location(s):
                self.stripes.append(s)
                bitval += 1 << s
        self.f.write(0x400007, bitval)

        if self.stripes == []:
            print("Warning: no stripe selected.")
        if self.full18bits == True and len(self.stripes) > 2 :
            print("Warning: attempting to read 18-bit data for 3 stripes, full image will not fit")
            self.imglines = 1000

        self.nchannels = 16*len(self.stripes)

    # --------------------------------------------------------------------
    def update_filetag(self, t):
        """
        Updates the filetag to the FPGA timer.
        :param t: int new numerical tag
        :return:
        """
        hextag = reb.generate_tag(t)
        self.imgtag = t
        self.fpga.set_time(hextag)

    def recover_filetag(self):
        """
        Reads the filetag from the FPGA timer and recovers imgtag if it is in the right format.
        Returns the tag.
        :return: string
        """
        t = self.fpga.get_time()
        tagstr = '0x%016x' % t
        todaystr = time.strftime('%Y%m%d', time.gmtime())
        if string.find(tagstr, todaystr) > -1:
            self.imgtag = int(tagstr[-5:], base=10)

        return tagstr

   # --------------------------------------------------------------------
    def REBpowerup(self):
        """
        Operations after powering the REB
        :return:
        """
        #specific to REB1
        self.cabac_reset()

        self.load_sequencer()
        #sets the default sequencer clock states to 0
        self.fpga.send_function(0, fpga0.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))

        print("REB ready to connect to CCD")

    def CCDpowerup(self):
        """
        Sequence to power up the CCD safely.
        """

        #starting drain voltages on CABAC
        drains = {"OD": 29, "GD": 24, "RD": 18}
        self.send_cabac_config(drains)

        time.sleep(1)

        #starting OG voltage on CABAC
        og = {"OG": 3.5}
        self.send_cabac_config(og)

        time.sleep(1)

        #sets clock rails
        dacs = {"V_SL": 0, "V_SH": 8.03, "V_RGL": 0, "V_RGH": 8.03, "V_PL": 0, "V_PH": 9.13}
        self.fpga.set_clock_voltages(dacs)

        time.sleep(1)

        #sets clock currents on CABAC
        iclock = {"IC": 255}
        self.send_cabac_config(iclock)

        time.sleep(1)

        #puts current on CS gate
        for stripe in self.stripes:
            self.fpga.set_current_source(0xfff, stripe)

        #rewrite default state of sequencer (to avoid reloading functions)
        self.fpga.send_function(0, self.seq.get_function(0))

        time.sleep(0.1)

        #now is the time to the backsubstrate voltage (elsewhere)
        print("CCD start-up sequence complete on REB, ready for Back Substrate.")

    def CCDshutdown(self):
        """
        Sequence to shut down the CCD safely
        """

        self.wait_end_sequencer()
        #Back-substrate first
        print("Back Substrate must be shut down before this.")
        time.sleep(3)

        #current source
        for stripe in self.stripes:
            self.fpga.set_current_source(0, stripe)

        time.sleep(0.5)

        #clock states to 0
        self.fpga.send_function(0, fpga0.Function( name="default state", timelengths={0: 2, 1: 0}, outputs={0: 0, 1: 0}))
        #currents on CABAC clocks to 0
        self.send_cabac_config({"IC": 0})
        #clock rails to 0
        self.fpga.set_clock_voltages({"V_SL": 0, "V_SH": 0, "V_RGL": 0, "V_RGH": 0, "V_PL": 0, "V_PH": 0})

        time.sleep(1)

        #currents on OG to 0
        self.send_cabac_config({"OG": 0})

        time.sleep(1)

        #drains to 0
        self.send_cabac_config({"OD": 0, "GD": 0, "RD": 0})

        print("CCD shutdown complete")

    # --------------------------------------------------------------------

    def load_sequencer(self, xmlfile=None):
        """
        Loads all sequencer content.
        :return:
        """
        if xmlfile:
            self.xmlfile = xmlfile

        self.seq = rebxml.fromxmlfile(self.xmlfile)  # use self.seq.program to track addresses
        self.fpga.send_sequencer(self.seq)
        try:
            self.exptime = self.get_exposure_time()
        except:
            print("Warning: could not find exposure subroutine in %s" % xmlfile)
        self.name = ""  # there is actually no way to access that from self.seq

    def select_subroutine(self, subname, repeat=1):
        """
        Modify the main subroutine to be a call (JSR) to the subroutine.
        """
        if self.seq.program == None:
            raise ValueError("No program with identified subroutines yet.")

        if not (self.seq.program.subroutines.has_key(subname)):
            raise ValueError("No subroutine '%s' in the FPGA program." % subname)

        first_instr = fpga0.Instruction0(
            opcode=fpga0.Instruction0.OP_JumpToSubroutine,
            address=self.seq.program.subroutines[subname],
            repeat=repeat)

        # load it at the very beginning of the program (rel addr 0x0)
        self.fpga.send_program_instruction(0x0, first_instr)
        self.seq.program.instructions[0x0] = first_instr  # to keep it in sync
        self.name = subname

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

        return float(iter) * self.exposure_unit  # in seconds

    def set_exposure_time(self, exptime):
        """
        Modifies exposure subroutines to last the given exposure time
        (input in seconds).
        :param exptime: float
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        exposureadd = self.seq.program.subroutines[self.exposuresub]
        newinstruction = self.seq.program.instructions[exposureadd]
        newinstruction.repeat = int(max(newiter, self.min_exposure))  # This does rewrite the seq.program too
        self.fpga.send_program_instruction(exposureadd, newinstruction)

    def set_dark_time(self, exptime):
        """
        Modifies 'dark' exposure (shutter closed) subroutines to last the given exposure time
        (input in seconds).
        :param exptime:
        """
        newiter = int(exptime / self.exposure_unit)
        # look up address of exposure subroutine
        # then get current instruction and rewrite the number of iterations only
        darkadd = self.seq.program.subroutines[self.darksub]
        newinstruction = self.seq.program.instructions[darkadd]
        newinstruction.repeat = int(max(newiter, 1))  # must not be 0 or sequencer gets stuck
        self.fpga.send_program_instruction(darkadd, newinstruction)


    # --------------------------------------------------------------------

    def get_input_voltages_currents(self):
        return self.fpga.get_input_voltages_currents()

    # --------------------------------------------------------------------

    def get_cabac_config(self):
        """
        read CABAC configuration.
        """
        for stripe in self.stripes:
            self.fpga.get_cabac_config(stripe)

    # --------------------------------------------------------------------

    def send_cabac_config(self, params):
        """
        Sets CABAC parameters defined in the params dictionay and writes to CABAC, then checks the readback.
        """
        for stripe in self.stripes:
            for param in iter(params):
                self.fpga.set_cabac_value(param, params[param], stripe)

            self.fpga.send_cabac_config(stripe)

            time.sleep(0.1)

            self.fpga.get_cabac_config(stripe)

            for param in iter(params):
                self.fpga.check_cabac_value(param, params[param], stripe)

    # --------------------------------------------------------------------

    def cabac_reset(self):
        """
        Puts all CABAC values at 0, then checks the readback into the params dictionay.
        """
        for stripe in self.stripes:
            self.fpga.reset_cabac(stripe)

        time.sleep(0.1)

        self.get_cabac_config()


    # --------------------------------------------------------------------
    def wait_end_sequencer(self):
        """
        Waits until the sequencer is not running anymore.
        """
        while self.fpga.get_state() & 4:  # sequencer status bit in the register
            time.sleep(1)

    def config_sequence(self, name, exptime, shutdelay=100):
        """
        Configure the programmed sequence. Used also to record parameters.
        """
        self.wait_end_sequencer()
        self.select_subroutine(name)

        if name in ["Bias", "Test", "Wait"]:
            self.shutdelay = 0
            self.exptime = 0
        else:
            self.shutdelay = shutdelay
            self.exptime = exptime
            if name == "Dark":
                self.set_dark_time(exptime)
            else:
                self.set_exposure_time(exptime)

    def execute_sequence(self):
        """
        Executes the currently loaded sequence.
        """
        self.wait_end_sequencer()
        self.tstamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.fpga.start()
        print("Starting %s sequence with %f exposure time." % (self.name, self.exptime))
        #freeze until image output (do not send commands while the COB is acquiring)
        time.sleep(self.exptime+3)

    def waiting_sequence(self, name="Wait"):
        """
        Lets CCD wait by clearing periodically until keyboard interrupt is sent.

        """
        self.config_sequence(name, 0)
        keepwaiting = True
        while keepwaiting:
            try:
                self.execute_sequence()
                time.sleep(60)
            except KeyboardInterrupt:
                keepwaiting = False

    # --------------------------------------------------------------------

    def make_img_name(self):
        return os.path.join(self.rawimgdir,'0x%016x.img' % self.f.get_time())

