import xmlrpclib
import time, os, sys

def connectSystems():
  kv = xmlrpclib.ServerProxy("http://localhost:8087/")
  kv.connect()
  triax = xmlrpclib.ServerProxy("http://localhost:8086/")
  triax.connect()
  ttl = xmlrpclib.ServerProxy("http://localhost:8083/")
  ttl.connect()
  xehg = xmlrpclib.ServerProxy("http://localhost:8089/")
  xehg.connect()
  return kv, triax, ttl, xehg

curdir =  os.getcwd()
kv, triax, ttl, xehg = connectSystems()

lines  = [ 365.01, 404.65, 435.84, 546.07 ]

inslit =  30
outslit = 30
minl =  544.0
maxl =  548.0
rate = 10.0 
nsamples = 10

sys.exit()

triax.setWavelength(minl)
while triax.status() == 0:
   time.sleep(1.0)
l  = triax.getWavelength()
triax.setInSlit(inslit)
while triax.status() == 0:
   time.sleep(1.0)
triax.setOutSlit(outslit)
while triax.status() == 0:
   time.sleep(1.0)

kv.setRate(rate)
kv.zeroCorrect()
kv.recordData("")
kv.recordData(curdir + "/" + "{0}_{1}_slit{3}_{4}_r{2}.txt".format(minl,maxl,rate,inslit,outslit))


while l < maxl:
   sys.stdout.write("{0}\r".format(l));sys.stdout.flush()
   kv.writeComment("wavelength: {0}".format(l))
   kv.startSequence(nsamples)
   while kv.status() > 0:
       time.sleep(0.5)
   triax.moveRelative(1)
   while triax.status() == 0:
       time.sleep(1.0)
   l = triax.getWavelength()
   
