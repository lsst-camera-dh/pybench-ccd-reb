#
# LSST / LPNHE
# Author: Laurent Le Guillou
#
"""
Testbench driver for the Keithley multimeter 6487 [power source] 
(through keithley (Edo) and XML-RPC)
keithley /dev/ttyS11 8088
"""
# common methods
#   [rc,string] connect()        rc=0 error, rc=1 OK, rc=2 warn, port already opened
#   void close()                 
#   string getModel()            returns the instrument's model or an empty string if no connection
#   int status()                 returns the instrument status (amps.):
#                                   0=not reading, 1=not connected, 2=acquiring continuous,
#                                   3=acquiring  a sequence
#   void setVerbose(bool)        puts software in verbose mode
#   void recordData(String)      records data (amps.) in String file if String is not empty, otherwise stops recording
#   void writeComment(String)    adds String to the header of the record file
#   help()                       this information

# current measurement related methods
#   zeroCorrect()                performs zero correct procedure
#   double getCurrent()          the last read value, instrument must be acquiring continuously
#   readContinuous(int)          -1 to stop, 0 to read fastest, other value = delay between reads
#   setRate(double)              sets read rate 0.01 --> 10.0 or 50.0 (if model is 6487)
#   startSequence(int)           begins acquiring a sequence, argument: number of data values to acquire
#   getSequence()                returns the list of read values (double)

# voltage source related methods (only 6487 model)
#   getVoltageRange              returns int 0: 10V 1: 50V 2: 500V
#   setVoltageRange              int argument [0-2]
#   getVoltage                   returns a double, preset output voltage
#   setVoltage                   double argument, [-70.0, 0.0]
#   getCurrentLimit              returns int 0: 25uA, 1: 250uA, 2: 2.5mA and 3: 25mA iff voltage range is 10V
#   setCurrentLimit              int argument [0-2,3]
#   sourceVoltage                int argument 0: stop sourcing, other value sources voltage
#   voltageStatus                returns int 0: not sourcing 1: sourcing

from driver import Driver

import xmlrpclib

# =======================================================================

class Instrument(Driver):


    currentlimits = { 2.5e-5 : 0,
                      2.5e-4 : 1,
                      2.5e-3 : 2,
                      2.5e-2 : 3 }

    currentlimits_reverse = {}
    for k, v in currentlimits.iteritems():
        currentlimits_reverse[v] = k
        
    # --

    voltageranges = {  10.0 : 0,
                       50.0 : 1,
                      100.0 : 2 }
    voltageranges_reverse = {}

    for k, v in voltageranges.iteritems():
        voltageranges_reverse[v] = k

    # ===================================================================
    #  Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)
        
        # self.identifier = identifier
        # self.host = host
        # self.device = device
        # self.port = port # XML-RPC port

        if 'host' not in kargs.keys():
            raise ValueError("host is requested")

        if 'devices' not in kargs.keys():
            raise ValueError("devices is requested")

        if 'port' not in kargs.keys():
            raise ValueError("port is requested")

        self.xmlrpc = xmlrpclib.ServerProxy("http://%s:%d/" % 
                                            (self.host, self.port))


    def open(self):
        """
        Open the hardware connection.
        """
        code, msg = self.xmlrpc.connect()


    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        Returns True if the hardware answers, False otherwise.
        """
        answer = self.checkConnection()

        if answer == "" or answer == ():
            return False

        if '6487' not in answer:
            return False
            
        return True


    def checkConnection(self):
        """
        Returns a NULL string or the instrument model name
        """
        return self.xmlrpc.getModel()


    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not(connected):
            raise IOError("Keithley Multimeter not connected.")

        Driver.register(self, bench)


    def close(self):
        """
        Close the hardware connection.
        """
        self.xmlrpc.close()
        # TODO: Check errors


    # ===================================================================
    #  Instrument specific methods
    # ===================================================================


    def status(self):
        """
        Return the status of the system.
        """
        return self.xmlrpc.status()

    # --------------------------------------------------------------

    def reset(self):
        """
        Reset the instrument to the factory default settings
        (with the exception of all remote interface settings).
        """
        # logging.info("Keithley.reset() called.")
        # result = self.xmlrpc.reset()
        # logging.info("Keithley.reset() done.")
        print "Not Yet implemented"
        # return result


    def clear(self):
        """
        Clear the instrument status.
        """ 
        # logging.info("Keithley.clear() called.")
        # result = self.xmlrpc.clear()
        # logging.info("Keithley.clear() done.")
        print "Not Yet implemented"
        # return result

    
    # ----------------------- Keithley generic command ------------------

    def send(self, command, timeout = 1.0):
        """
        Send a command through the serial port.
        Read the answer from the serial port.
        Return it as a string.

        If <timeout> is specified, the function will wait
        for data with the specified timeout (instead of the default one). 
        """

        # logging.info("Keithley.send() called.")
        # logging.info("  command = [%s]" % command)
        answer = self.xmlrpc.send(command, timeout)
        # logging.info("  answer = [%s]" % answer)
        # logging.info("Keithley.send() done.")
        esr = self.xmlrpc.get_error_status()
        if esr != 0:
            raise IOError("Keithley command [%s] failed: error code ESR = %d." 
                          % (command, esr))

        return answer

    # ----------------------- Keithley identification -------------------

    def get_serial(self):
        """
        Return the identification string of the Keithley.
        """
        # logging.info("Keithley.get_serial() called.")
        serial = self.xmlrpc.get_serial()
        # logging.info("  serial = [%s]" % serial)
        # logging.info("Keithley.get_serial() done.")
        return serial

    # ----------------------- Various methods ---------------------------

    def scroll_text(self, msg):
        """
        Scroll text 'msg' on the Multimeter display.
        For debug purpose only.
        """
        # logging.info("Keithley.scroll_text() called.")
        result = self.xmlrpc.scroll_text(msg)
        # logging.info("Keithley.scroll_text() done.")
        return result

    # ===================================================================
    #  Voltage source methods
    # ===================================================================

    # "SOUR:VOLT:RANG 50"
    # "SOUR:VOLT:ILIM 2.5e-05"
    # "SOUR:VOLT -40"
    # "SOUR:VOLT:STAT ON"
    # "SOUR:VOLT:STAT OFF"

    # ----- Current settings

    def getCurrentLimit(self):
        """
        Return current limit (in A)
        """
        lim = self.xmlrpc.getCurrentLimit()
        return self.currentlimits_reverse[lim]

    
    def setCurrentLimit(self, limit):
        """
        argument : 25uA  (2.5e-5)
                   250uA (2.5e-4)
                   2.5mA (2.5e-3)
                   25mA  (2.5e-2) if voltage range is 10V
        """
        lim = self.currentlimits[limit]
        self.xmlrpc.getCurrentLimit(limit)
    
    # ----- Voltage settings
 
    def getVoltageRange(self):
        """
        Return voltage range in Volts.
        """
        lim = self.xmlrpc.getVoltageRange()
        return self.voltageranges_reverse[lim]

    
    def setVoltageRange(self, voltagerange):
        """
        argument : 10V, 50V or 500V
        """
        lim = self.voltageranges[limit]
        self.xmlrpc.setVoltageRange(limit)

    # ------

    def getVoltage(self):
        """
        Return voltage setting in Volts.
        """
        command = "SOUR:VOLT?"
        # print command
        answer = float(self.send(command))
        return answer

    
    def setVoltage(self, voltage):
        """
        Set voltage for the voltage source.
        """
        command = "SOUR:VOLT %f" % float(voltage)
        # print command
        answer = self.send(command)
        return answer

    # source enable and source status

    def voltageStatus(self):
        """
        Check the voltage source status (0 OFF/ 1 ON).
        """
        command = "SOUR:VOLT:STAT?"
        # print command
        answer = int(self.send(command))
        return answer


    def sourceVoltage(self, on):
        """
        Enable/disable the voltage source (0 OFF/ 1 ON).
        """
        arg = "OFF"
        if on:
            arg = "ON"
    
        command = "SOUR:VOLT:STAT "  + arg
        # print command
        answer = self.send(command)
        return answer


    def enable(self):
        """
        Enable the voltage source.
        """
        self.sourceVoltage(1)


    def disable(self):
        """
        Disable the voltage source.
        """
        self.sourceVoltage(0)


    # ===================================================================
    # High Level command for the BackSubstrate Power
    # ===================================================================
    



    # ===================================================================
    #  Meta data / state of the instrument 
    # ===================================================================


    def get_meta(self):
        """
        Returns meta data describing the current state
        of the instrument. 
        Useful to fill the FITS headers.
        """

        # keys : specify the key order
        keys = ['MODEL',
                'DRIVER',
                'VOLTRANG',
                'VOLTILIM',
                'VOLTAGE',
                'VOLTSRC']

        # comments : meaning of the keys
        comments = {
            'MODEL'    : 'Instrument model',
            'DRIVER'   : 'Instrument software driver', 
            'VOLTRANG' : '[V] Voltage range in Volts',
            'VOLTILIM' : '[V] Volt. Source current limit',
            'VOLTAGE'  : '[V] Voltage setting',
            'VOLTSRC'  : '[V] Voltage source on/off'
            }

        values = {
            'MODEL'    : self.get_serial(),
            'DRIVER'   : 'keithley-server / power_backsubstrate_ks',
            'VOLTRANG' : self.getVoltageRange(),
            'VOLTILIM' : self.getCurrentLimit(),
            'VOLTAGE'  : self.getVoltage(),
            'VOLTSRC'  : self.voltageStatus() 
            }

        return keys, values, comments

    # ===================================================================


# class BackSubstrate():
#     """
#     Managing back-substrate voltage controlled by Keithley 6487
#     """
#     setvoltbss = 0  # desired voltage setting (independent of actual value)
#     count = 1  # number of measures for monitoring
#     rate = 1.0  # monitoring rate
#     name = "Keithley 6487"

#     def __init__(self):
#         self.server = xmlrpclib.ServerProxy("http://lpnlsst:8088/")
#         self.server.connect()
#         check_xmlrpc(self.server, "6487")

#     def config(self, voltage=0):
#         """
#         Configuration of voltage, current limits and current readout.
#         """

#         if abs(voltage) < 50:
#             range = 1
#         else:
#             range = 2  # 500 V
#         self.server.setVoltageRange(range)

#         self.set_volt(voltage)
#         #self.selectCurrent(2e-5)  # selecting current range: not implemented yet
#         self.server.zeroCorrect()
#         self.server.setCurrentLimit(0)  # 25 uA
#         self.server.setRate(self.rate)

#     def check_config(self):
#         inti = self.server.getCurrentLimit()
#         if inti != 0:
#             raise IOError("Wrong current limit setting on bss: %d" % inti)
#         # can add check on range (getVoltageRange) and setvoltbss (getVoltage)

#     def set_volt(self, voltage):
#         """
#         Changes voltage without changing configuration
#         """
#         if voltage < 0:
#             self.server.setVoltage(float(voltage))
#             self.setvoltbss = voltage
#         else:
#             errorstr = "Asked for a positive back-substrate voltage (%f), not doing it. " % voltage
#             if stand_alone:
#                 print(errorstr)
#             else:
#                 raise ValueError(errorstr)

#     def enable(self):

#         self.server.sourceVoltage(1)

#         time.sleep(30)

#         #check
#         ena = self.server.voltageStatus()
#         if ena != 1:
#             raise IOError("Error on back-substrate voltage: not enabled.")

#     def disable(self):

#         self.server.sourceVoltage(0)
#         time.sleep(10)
#         while self.server.voltageStatus() != 0:
#             time.sleep(1)

#     def get_current(self):
#         """
#         Get a single current reading.
#         :return: double
#         """
#         self.count = 1
#         self.server.startSequence(1)
#         while self.server.status() == 3:  # TBC
#             time.sleep(1)

#         return self.server.getSequence()[0]

#     def set_monitor_rate(self, rate):
#         """
#         Sets rate of monitoring to a new value.
#         Useful to do before long exposures.
#         :param rate:
#         :return:
#         """
#         self.rate = rate
#         self.server.setRate(self.rate)

#     def start_monitor(self, exptime):
#         """
#         Configures back-substrate current monitoring for an exposure
#         :param exptime: double
#         """
#         self.count = int(exptime * self.rate)+ 1
#         self.server.startSequence(self.count)

#     def read_monitor(self):
#         """
#         Reads the latest sequence from the monitoring photodiode. Averages the results after eliminating outliers.
#         :return: double
#         """
#         while self.server.status() == 3:
#             time.sleep(1)
#         readarray = np.array(self.server.getSequence())
#         av_read = readarray.mean()

#         return av_read

#     def get_operating_header(self):
#         """
#         Gets voltage and current on back substrate in header dictionary format.
#         : return : dict
#         """
#         vss = "0.0"
#         if self.server.voltageStatus():
#             # vss = "{:.2f}".format(self.server.getVoltage())
#             vss = "%.2f" % self.server.getVoltage()
#         # otherwise back-substrate voltage is off
#         if self.count > 1:
#             imon = self.read_monitor()
#         else :
#             imon = self.get_current()
#         iss = ":%.3E" % imon

#         return {"V_BSS": vss, "I_BSS": iss}

