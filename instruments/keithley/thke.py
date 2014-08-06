from PySide.QtCore import QObject
from PySide.QtCore import Signal
from PySide.QtCore import QThread
from PySide.QtCore import QCoreApplication
from PySide.QtGui import QApplication
from PySide.QtCore import QEventLoop
from PySide.QtCore import Slot
from KeithleyThread import KeithleyThread

import datetime, time, sys, random

class MyProgram(QThread):
  signalGetCurrent1              = Signal()
  signalGetCurrentContinuous1    = Signal()
  signalGetCurrentContinuous2    = Signal()

  def __init__(self, parent=None):
     super(MyProgram,self).__init__()
     self.signalGetCurrent1.connect(keithley1.sr.getCurrent)
     self.signalGetCurrentContinuous1.connect(keithley1.sr.getCurrentContinuous)
     self.signalGetCurrentContinuous2.connect(keithley2.sr.getCurrentContinuous)
 
  def run(self):
    keithley1.send("CURR:DC:NPLC 0.1")
    keithley2.send("CURR:DC:NPLC 0.1")
    self.signalGetCurrentContinuous1.emit()
    #self.signalGetCurrentContinuous2.emit()
    for n in range(2, 10):
      keithley2.getSequence(10)
      print keithley2.answer

      time.sleep(1)

if __name__ == '__main__':
  #app = QCoreApplication(sys.argv)
  app = QApplication(sys.argv)
  keithley1 = KeithleyThread("k1",3250,"/dev/ttyS0")
  keithley2 = KeithleyThread("k2",2500,"/dev/ttyUSB1")

  myProgram = MyProgram()

  keithley1.start()
  keithley2.start()
  myProgram.start()

  sys.exit(app.exec_())


