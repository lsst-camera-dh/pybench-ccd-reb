import matplotlib.pyplot as plt
import numpy as np
from matplotlib.mlab import griddata
import sys
if len(sys.argv)>1:
    filename = sys.argv[1]
else:
    filename = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/map-pos-01-map-01.data"
a = np.fromfile(filename, sep =' ')
b = a.reshape(a.shape[0]/3, 3)
c = np.transpose(b)
X = c[0]
Y = c[1]
Z = c[2]
xi = np.linspace(min(X), max(X))
yi = np.linspace(min(Y), max(Y))
X, Y = np.meshgrid(xi, yi)
Z = griddata(c[0], c[1], c[2], xi, yi)

fig = plt.figure()
ax=plt.subplot(111)
im =ax.pcolor(X,Y,Z)
ax.set_xlabel("X")
ax.set_ylabel("Y")
bar =fig.colorbar(im)
bar.set_label("photodiode current")
# plt.show()
fig.savefig(filename[:-5]+"_Map2d.png")
