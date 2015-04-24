import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
filename = "/home-local/karkar/dataLSST/metrology/2015-04-23/DKD-PhD-Laser-fluxes-2015-04-23T16:36:46.289969.data"
c = np.loadtxt(filename, comments='#', delimiter= ' ' , unpack=True, ndmin=0)
time = c[0];ch = c[1]; lasercurrent= c[2]; laserpower=c[3] ; DKDflux= c[4]/13; PhDFlux = c[5]/100
print c.shape

for i in [1,2,3,4]:
  plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'DKDflux VS laserpower',numpoints = 1)
plt.savefig('DKDfluxVSlaserpower')
plt.show()

for i in [1,2,3,4]:
  plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'PhDFlux VS laserpower', numpoints = 1)
plt.savefig('PhDfluxVSlaserpower')
plt.show()

for i in [1,2,3,4]:
  plt.plot(lasercurrent[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'DKDflux VS lasercurrent',numpoints = 1)
plt.savefig('DKDfluxVSlasercurrent')
plt.show()

for i in [1,2,3,4]:
  plt.plot(lasercurrent[(ch==i) & (laserpower>0.5) ], PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'PhDFlux VS lasercurrent',numpoints = 1)
plt.savefig('PhDfluxVSlasercurrent')
plt.show()

for i in [1,2,3,4]:
  plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)]/ PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'DKDflux/PhDFlux VS laserpower',numpoints = 1)
plt.savefig('DKDfluxOverPhDFluxVSlaserpower')
plt.show()

for i in [1,2,3,4]:
  plt.plot(lasercurrent[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)]/ PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
plt.legend(title = 'DKDflux/PhDFlux VS lasercurrent',numpoints = 1)
plt.savefig('DKDfluxOverPhDFluxVSlasercurrent')
plt.show()



for i in [1,2,3,4]:
  plt.plot(time[ch==i], laserpower[ch==i] , label="laser channel {}".format(i))
plt.legend(title = 'laserpower VS time',numpoints = 1)
plt.savefig('laserpowerVStime')
plt.show()

for i in [1,2,3,4]:
  plt.plot(time[ch==i], lasercurrent[ch==i] , label="laser channel {}".format(i))
plt.legend(title = 'lasercurrent VS time',numpoints = 1)
plt.savefig( 'lasercurrentVStime')
plt.show()



