import serial, sys, re

class LaserThorlabs(object):
  """ class for the Thorlabs 4 channel MCLS1 laser """
  answer="start"  
  device=""
  def __init__(self, dev = None):
    try:
      self.serialport = serial.Serial()
      if dev is None:
        self.device = "/dev/ttyUSB0"
      else:
        self.device = dev
    except serial.SerialException as e:
      print("creating SerialPort: '{}':\n\t{}".format(dev, e))

  def connectInstrument(self):
    self.serialport.port = self.device
    self.serialport.baudrate = 115200
    self.serialport.timeout = 2
    try:
      self.serialport.open()
    except serial.SerialException as e:
      print("opening SerialPort: '{}':\n\t{}".format(self.device, e))

  def disconnectInstrument(self):
    self.serialport.close()

  def send(self,command):
    try:
      self.serialport.write(command + "\r")
      endofline = False
      self.answer = ""
      while True:
        byte = self.serialport.read()
        if byte == ">" or byte == "<":
          endofline = True
        elif byte == " " and endofline:
          break
        elif byte == "\r":
          self.answer += " "
        else:
          self.answer += byte
    except (serial.SerialException, ValueError, AttributeError) as e:
      print("reading/Writing SerialPort: '{}':\n\t{}".format(self.device, e))


  def getId(self):
    self.send("id?")

  def getChannelSpecs(self):
    self.send("specs?")

  def selectChannel(self,channel):
    self.send("channel=" + str(channel))

  def enableChannel(self,channel):
    self.send("channel=" + str(channel))
    self.send("enable=1")

  def disableChannel(self,channel):
    self.send("channel=" + str(channel))
    self.send("enable=0")

  def enableLaser(self):
    self.send("system=1")

  def disableLaser(self):
    self.send("system=0")

