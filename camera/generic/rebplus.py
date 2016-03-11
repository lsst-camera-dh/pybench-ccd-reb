#
# LSST / LPNHE
# Author: Claire Juramy, Laurent Le Guillou
#
"""
Extension of the generic REB object to use the sequencer pointer features.
This takes REB as a parent and overloads the REB methods that depend on pointers,
plus adds in pointer manipulation.
To be used as parent in specific REB-derived classes instead of the original REB
generic object.
"""

from reb import *
import rebtxt

class REBplus(REB):
    # =======================================================================
    # These become the possible targets of the Exposure pointer
    REB.exposuresub = "ExposureFlush"
    REB.darksub = "SerialFlush"

    # ===================================================================

    def __init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0]):
        REB.__init__(self, reb_id=2,  ctrl_host=None, stripe_id=[0])
        # parameters are the same as the parent at initialization
        # will be filled when loading the sequencer
        # keeping 'xmlfile' as name for sequencer file

    def read_sequencer_file(self, xmlfile):
        """
        Reads sequencer file to internal variable self.seq.
        :return:
        """
        self.xmlfile = xmlfile

        self.seq = rebtxt.fromtxtfile(os.path.join(self.xmldir, self.xmlfile))

    def load_sequencer(self, xmlfile=None):
        """
        Loads all sequencer content.
        :return:
        """
        if xmlfile:
            self.read_sequencer_file(xmlfile)
        # otherwise use self.seq already loaded
        else:
            if not self.seq:
                self.read_sequencer_file(self.xmlfile)

        self.wait_end_sequencer()
        self.fpga.send_sequencer(self.seq)

        # ! change of name compared to XML
        # also change of convention: everything is a window now
        self.imglines = self.seq.parameters['ReadRows']
        self.imgcols = self.seq.parameters['ReadCols']

        try:
            self.exptime = self.get_exposure_time()
        except:
            print("Warning: could not find exposure subroutine in %s" % xmlfile)

        # select a subroutine to fill self.seqname
        self.select_subroutine('Bias')

    def set_pointer(self, pointername, newtarget):
        """
        Set a pointer to a new target and writes it.
        Needs a loaded sequencer.
        :param pointername:
        :param newtarget:
        :return:
        """
        if pointername not in self.seq.pointers:
            raise ValueError('Trying to write undefined pointer: %s' % pointername)
        seqpointer = self.seq.pointers[pointername]

        if seqpointer.pointer_type in seqpointer.Repeat_pointers:
            # no need to compile if it is a repetition
            seqpointer.value = newtarget
        elif seqpointer.pointer_type == 'PTR_FUNC':
            # accepts name or number
            if isinstance(newtarget, int):
                seqpointer.value = newtarget
                seqpointer.target = self.seq.functions[seqpointer.value].name
            else:
                # need to look up the function
                if newtarget not in self.seq.functions_desc:
                    raise ValueError("Trying to point to undefined function %s" % newtarget)
                seqpointer.target = newtarget
                seqpointer.value = self.seq.functions_desc[seqpointer.target]['idfunc']
        else:
            # need to look up the subroutine
            if newtarget not in self.seq.program.subroutines:
                raise ValueError("Trying to point to undefined subroutine %s" % newtarget)
            seqpointer.target = newtarget
            seqpointer.value = self.seq.program.subroutines[seqpointer.target]

        # write to FPGA
        self.fpga.send_pointer(seqpointer)

    def get_pointer(self, pointername, readback=False):
        """
        Gets the value of pointer, depending on type.
        :param pointername:
        :return:
        """
        if pointername not in self.seq.pointers:
            raise ValueError('Trying to read undefined pointer: %s' % pointername)
        seqpointer = self.seq.pointers[pointername]

        if readback:
            # checks from FPGA
            readvalue = self.fpga.read_pointer(seqpointer)
            if readvalue != seqpointer.value:
                print('Warning: value in pointer %s is %d for expected %d' % (pointername, readvalue, seqpointer.value))

        if seqpointer.pointer_type in seqpointer.Repeat_pointers:
            content = seqpointer.value
        else:
            # returns number/address and name
            content = (seqpointer.value, seqpointer.target)

        return content

    def select_subroutine(self, subname, repeat=1):
        """
        Modify the main subroutine (content of the Main pointer).
        """
        if self.seq.program is None:
            raise ValueError("No program with identified subroutines yet.")

        self.wait_end_sequencer()
        self.set_pointer('Main', subname)  # will also tests the subroutine exists
        self.seqname = subname  # keep it compatible with non-pointer version
        print('Sequencer program set to %s' % subname)

    def get_exposure_time(self, darktime=False):
        """
        Gets the exposure time from the subroutines in memory.
        darktime is kept for compatibility but not in use anymore.
        :param darktime: boolean
        """
        iterexp = self.get_pointer('ExposureTime', readback=True)
        # with readback

        self.exptime = float(iterexp) * self.exposure_unit  # in seconds

        return self.exptime

    def set_exposure_time(self, exptime):
        """
        Modifies exposure pointer to last the given exposure time (input in seconds).
        :ptype exptime: float
        """
        newiter = int(exptime / self.exposure_unit)
        newrepeat = int(max(newiter, self.min_exposure))

        self.wait_end_sequencer()
        self.set_pointer('ExposureTime', newrepeat)

        self.exptime = newrepeat * self.exposure_unit
        print('Set exposure time to %f s' % self.exptime)

    def set_dark_time(self, exptime):
        """
        Modifies exposure to last the given time (input in seconds).
        :param exptime:
        """
        newrepeat = int(exptime / self.exposure_unit)
        # 0 iteration should be acceptable (not tested)

        self.wait_end_sequencer()
        self.set_pointer('ExposureTime', newrepeat)

        self.exptime = newrepeat * self.exposure_unit
        print('Set dark time to %f s' % self.exptime)

    # --------------------------------------------------------------------

    def config_sequence(self, name, exptime=0.1, shutdelay=100):
        """
        Configure the programmed sequence. Used also to record parameters.
        """
        # wait_end_sequencer is now included in select_subroutine
        self.select_subroutine(name)

        if name in ["Bias", "Test", "Wait", "ClearBias", 'InfiniteWait']:
            self.shutdelay = 0
            self.exptime = 0
        else:
            self.shutdelay = shutdelay
            self.exptime = exptime
            if name == "Dark":
                self.set_dark_time(exptime)
                self.set_pointer('Exposure', self.darksub)

            else:
                self.set_exposure_time(exptime)
                self.set_pointer('Exposure', self.exposuresub)

