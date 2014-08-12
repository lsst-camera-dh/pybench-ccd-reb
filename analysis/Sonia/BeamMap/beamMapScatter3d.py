import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import sys
if len(sys.argv)>1:
    filename = sys.argv[1]
else:
    filename = "/home/karkar/fromXPS/LSST/dataTestCCD/beamMaps/map-pos-01-map-01.data"

a = np.fromfile(filename, sep =' ')
b = a.reshape(a.shape[0]/3, 3)
c = np.transpose(b)
fig = plt.figure()
ax = fig.gca(projection='3d')
im = ax.scatter(c[0],c[1],c[2],c =c[2], cmap=mpl.cm.rainbow, s = 150 )
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Photodiode current")
bar = fig.colorbar(im)
bar.set_label("photodiode current")
# plt.show()
fig.savefig(filename[:-5]+"_Scatter3d.png")
