from PySide import QtCore # was: from PySide.QtCore import *
from PySide import QtGui  # idem
from PySide.QtCore import QObject
from PySide.QtCore import Signal
from PySide.QtCore import QEventLoop
from PySide.QtCore import Slot
from laserthorlabs import LaserThorlabs

import time, sys, random

class laserThread(QtCore.QThread):
  dataReady = Signal(object,object)
  data=-1.0
  l = LaserThorlabs("/dev/ttyUSB8")

  def __init__(self, parent=None):
    super(laserThread, self).__init__(parent)

  def run(self):
#    self.l = LaserThorlabs("/dev/ttyUSB8")
    self.l.connect()
    self.timer = QtCore.QTimer()
    self.timer.timeout.connect(self.readTimeout)
    self.timer.start(1000)
    self.exec_()

  @QtCore.Slot(str)
  def readTimeout(self):
    self.data = random.random()
    self.l.getId()
    self.dataReady.emit(self.data,self.l.answer) 


class Laser(QtGui.QWidget,QObject):
  def __init__(self):
    self.thread = laserThread()
    self.thread.dataReady.connect(self.get_data,QtCore.Qt.QueuedConnection)
    #self.thread.start()

  @QtCore.Slot(str)
  def get_data(self, data, answer):
    print "wid: " + str(data) + " " + answer

if __name__ == '__main__':
  app = QtCore.QCoreApplication(sys.argv)
  l = Laser()
  l.thread.start()
  print l.thread.l.answer
  sys.exit(app.exec_())


