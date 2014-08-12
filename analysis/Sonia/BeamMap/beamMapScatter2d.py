import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

filename = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/map-pos-01-map-01.data"

a = np.fromfile(filename, sep =' ')
b = a.reshape(a.shape[0]/3, 3)
c = np.transpose(b)
fig = plt.figure()
ax = plt.subplot(111)
im = ax.scatter(c[0],c[1],c =c[2], cmap=mpl.cm.rainbow, s = 400)
ax.set_xlabel("X")
ax.set_ylabel("Y")
bar = fig.colorbar(im)
bar.set_label("photodiode current")
# plt.show()
fig.savefig(filename[:-5]+"_Scatter2d.png")
