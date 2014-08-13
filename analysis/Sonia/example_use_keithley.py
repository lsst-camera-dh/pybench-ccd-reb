import xmlrpclib

k = xmlrpclib.ServerProxy("http://lpnlsst:8102/")

k.open() # establish the connection between lpnlsst and the Keithley

k.reset() # restaure les réglages d'usine (brutal)

# choix de la mesure et du calibre
k.send("CURR:RANG " % "2e-10")
k.send("FUNC 'CURR:DC'")
k.send("SYST:ZCH OFF")
k.send("TRIG:COUN %d" % 20)
k.send(":SENS:CURR:NPLC 1") # 1 seems to be the default
k.send(":DISP:ENAB OFF") # turn off the display on the instrument

data_string = k.send("READ?")
parts = data_string.split(',') # return a list of timestamps and values
currents = np.array([float(i) for i in parts])[0::3]