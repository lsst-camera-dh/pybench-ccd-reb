from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.mlab import griddata
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
ax = fig.gca(projection='3d')
surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,linewidth=0, antialiased=False)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Photodiode current")
fig.colorbar(surf, shrink=0.5, aspect=5)
plt.show()

