import serial
import sys
from select import select

ser = serial.Serial('/dev/ttyACM0', 19200,timeout=1)
timeout = 1

while True:
    line = ser.readline()
    print line
    rlist, _, _ = select([sys.stdin], [], [], timeout)
    if rlist:
        s = sys.stdin.readline()
        ser.write(s)
    



