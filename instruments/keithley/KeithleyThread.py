from PySide.QtCore import QObject
from PySide.QtCore import QThread
from PySide.QtCore import QTimer
from PySide.QtCore import Signal
from PySide.QtCore import Slot
from Keithley import Keithley
import datetime, time, sys, random


class SignalReceiver(QObject):
  def __init__(self,keithley):
    super(SignalReceiver,self).__init__()
    self.keithley= keithley
 
  @Slot()
  def getCurrentContinuous(self):
    self.timer = QTimer()
    self.timer.timeout.connect(self.getCurrent)
    self.timer.start(self.keithley.readTimeout)
 
  @Slot()
  def getCurrent(self):                   
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    self.keithley.getCurrent()
    print self.keithley.name + " reading current: " + str(st) + " " + str(self.keithley.current)


class KeithleyThread(Keithley,QThread):
  current=None
  timeout=0

  def __init__(self, name, readTimeout=1000, dev = None, parent=None):
    Keithley.__init__(self,dev)
    QThread.__init__(self)
    self.name = name
    self.readTimeout = readTimeout
    self.connectInstrument()
    self.selectCurrent()
    self.zeroCorrect()
    self.sr = SignalReceiver(self)
    self.sr.moveToThread(self)

