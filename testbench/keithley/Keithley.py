import serial, sys, re

class Keithley(object):
  """ class for the Keithley meters """
  answer="initial answer..."  
  model=""
  current=""
  volt=""
  def __init__(self, dev = None):
    try:
      self.serialport = serial.Serial()
      if dev is None:
        self.device = "/dev/ttyS4"
      else:
        self.device = dev
    except serial.SerialException as e:
      print("creating SerialPort: '{}':\n\t{}".format(dev, e))

  def connectInstrument(self):
    self.serialport.port = self.device
    self.serialport.baudrate = 19200
    self.serialport.timeout = 2
    try:
      self.serialport.open()
      self.send("*RST")
      self.getModel()

    except serial.SerialException as e:
      print("opening SerialPort: '{}':\n\t{}".format(self.device, e))

  def disconnectInstrument(self):
    self.serialport.close()

  def selectOutputVoltageRange(self,range,ilim = 2.5e-3):
    if self.model == "6487":
      self.send("SOUR:VOLT:RANG " + str(range))
      self.send("SOUR:VOLT:ILIM " + str(ilim))

  def setOutputVoltage(self,value):
    self.send("SOUR:VOLT " + str(value))
  
  def voltageSourceOperate(self,value):
    if value:
      self.send("SOUR:VOLT:STAT ON")
    else:
      self.send("SOUR:VOLT:STAT OFF")

  def selectCurrent(self, range = None):
    if self.model != "6485":
      self.send("FUNC 'CURR:DC'")
    self.send("FORM:ELEM READ,TIME")
    if not range:
      self.send("CURR:RANG:AUTO ON")
    else:
      self.send("CURR:RANG " + str(range))

  def zeroCorrect(self):
    self.send("SYST:ZCH ON")
    if self.model == "6514":
      self.send("CURR:RANG 20e-12")
    elif self.model == "6485" or self.model == "6487":
      self.send("CURR:RANG 2e-9")
    self.send("INIT")
    self.send("SYST:ZCOR:ACQ")
    self.send("SYST:ZCOR ON")
    self.send("CURR:RANG:AUTO ON")
    self.send("SYST:ZCH OFF")

  def getSequence(self,N):
    self.send("TRAC:CLEAR")
    self.send("TRIG:COUN " + str(N))
    self.send("TRAC:POIN " + str(N))
    self.send("TRAC:FEED SENS")
    self.send("TRAC:FEED:CONT NEXT")
    self.send("INIT")
    self.send("TRAC:DATA?")

  def getCurrent(self):
    self.send("READ?")
    self.current = self.answer

  def getModel(self):
    self.send("*IDN?")
    p = re.compile(r',MODEL (\d+),')
    m = p.search(self.answer)
    self.model = m.group(1)
  
  def getOutputVoltage(self):
    if self.model == "6487":
      self.send("SOUR:VOLT?")
      self.volt = self.answer
  
  def send(self,command):
    try:
      self.serialport.write(command + "\n")
      if not command.endswith("?"):
        self.serialport.write("SYST:ERR?" + "\n")
      self.answer = ""
      while True:
        byte = self.serialport.read()
        if byte == "\n":
          break
        else:
          self.answer += byte
    except (serial.SerialException, ValueError, AttributeError) as e:
      print("reading/writing SerialPort: '{}':\n\t{}".format(self.device, e))


