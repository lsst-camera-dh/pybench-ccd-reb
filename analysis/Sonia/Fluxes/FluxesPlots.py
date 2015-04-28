import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
# filename = "/home-local/karkar/dataLSST/metrology/2015-04-23/DKD-PhD-Laser-fluxes-2015-04-23T16:36:46.289969.data"
# c = np.loadtxt(filename, comments='#', delimiter= ' ' , unpack=True, ndmin=0)
# time = c[0];ch = c[1]; lasercurrent= c[2]; laserpower=c[3] ; DKDflux= c[4]/13; PhDFlux = c[5]/100

def doPlot(X, Y, mytitle, ch,laserpower, prefix):

    imagename = mytitle.replace(" ","")
    print prefix+"_"+imagename+".png"

    channellist = [1,2,3,4]
    for channel in channellist:
      cutcondition = (ch==channel)
      plt.plot(X[cutcondition], Y[cutcondition], label="laser channel {}".format(channel), marker = "*", markeredgecolor= 'None', linewidth = 0)
    plt.grid(True)
    # plt.set_xlabel("X")
    # plt.set_ylabel("Y")
    plt.legend(title = mytitle,numpoints = 1)
    plt.savefig(prefix+"_"+imagename+".png")
    plt.show()
    plt.close()



# for i in [1,2,3,4]:
#   plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'DKDflux VS laserpower',numpoints = 1)
# plt.savefig('DKDfluxVSlaserpower')
# plt.show()



# for i in [1,2,3,4]:
#   plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'PhDFlux VS laserpower', numpoints = 1)
# plt.savefig('PhDfluxVSlaserpower')
# plt.show()

# for i in [1,2,3,4]:
#   plt.plot(time[(ch==i) & (laserpower>0.) ], DKDflux[(ch==i) & (laserpower>0.)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'DKDflux VS lasercurrent',numpoints = 1)
# plt.savefig('DKDfluxVStime')
# plt.show()

# for i in [1,2,3,4]:
#   plt.plot(lasercurrent[(ch==i) & (laserpower>0.5) ], PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'PhDFlux VS lasercurrent',numpoints = 1)
# plt.savefig('PhDfluxVSlasercurrent')
# plt.show()

# for i in [1,2,3,4]:
#   plt.plot(laserpower[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)]/ PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'DKDflux/PhDFlux VS laserpower',numpoints = 1)
# plt.savefig('DKDfluxOverPhDFluxVSlaserpower')
# plt.show()

# for i in [1,2,3,4]:
#   plt.plot( PhDFlux[(ch==i) & (laserpower>0.)],DKDflux[(ch==i) & (laserpower>0.)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)

#   plt.legend(title = 'DKDflux VS PhDFlux ',numpoints = 1)
#   plt.savefig('DKDfluxVSPhDFlux{}'.format(i))
#   plt.show()


# for i in [1,2,3,4]:
#   plt.plot(lasercurrent[(ch==i) & (laserpower>0.5) ], DKDflux[(ch==i) & (laserpower>0.5)]/ PhDFlux[(ch==i) & (laserpower>0.5)], label="laser channel {}".format(i), marker = "*", markeredgecolor= 'None', linewidth = 0)
# plt.legend(title = 'DKDflux/PhDFlux VS lasercurrent',numpoints = 1)
# plt.savefig('DKDfluxOverPhDFluxVSlasercurrent')
# plt.show()



# for i in [1,2,3,4]:
#   plt.plot(time[ch==i], laserpower[ch==i] , label="laser channel {}".format(i))
# plt.legend(title = 'laserpower VS time',numpoints = 1)
# plt.savefig('laserpowerVStime')
# plt.show()

# for i in [1,2,3,4]:
#   plt.plot(time[ch==i], lasercurrent[ch==i] , label="laser channel {}".format(i))
# plt.legend(title = 'lasercurrent VS time',numpoints = 1)
# plt.savefig( 'lasercurrentVStime')
# plt.show()



