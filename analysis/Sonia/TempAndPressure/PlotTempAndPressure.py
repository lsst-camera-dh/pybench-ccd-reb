__author__ = 'karkar'
import matplotlib.pyplot as plt
import numpy as np
def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.itervalues():
        sp.set_visible(False)


dataDir =  "/home/karkar/fromXPS/LSST/"
Tempfilename = "temp_shutdown_12august2014.txt"
Presfilename = "pressure_temp_shutdown_12august2014.txt"
t = np.genfromtxt(dataDir+Tempfilename, usecols= (1,2))
pow = np.genfromtxt(dataDir+Tempfilename, usecols= (3))
p = np.genfromtxt(dataDir+Presfilename, usecols = (1))
fig = plt.figure("Temperature shutdown August 12")
fig.subplots_adjust(right=0.75)
ax = plt.subplot(111)
plt.grid(True)
#print p.shape
timeaxis = 10*(np.arange(p.shape[0]))/3600.
#print timeaxis.shape
p1, =ax.plot( timeaxis, p, 'red')
ax.semilogy()
ax.set_xlabel("Hours")
ax.set_ylabel("mBar", color = p1.get_color())
ax.yaxis.label.set_color(p1.get_color())
ax.tick_params(axis='y', colors=p1.get_color())
ax2 = ax.twinx()
#print t.shape
p2,p3, = ax2.plot(timeaxis[:t.shape[0]], t)
ax2.set_ylabel("C", color = p2.get_color())
ax2.yaxis.label.set_color(p2.get_color())
ax2.tick_params(axis='y', colors=p2.get_color())
#ax3 = ax.twinx()
#ax3.spines["right"].set_position(("axes", 1.2))
#make_patch_spines_invisible(ax3)
#ax3.spines["right"].set_visible(True)
#ax3.plot(range(t.shape[0]),pow, label= "heating power")

#plt.show()
fig.savefig(dataDir+"TemperatureAndPressure2014August12.png")

