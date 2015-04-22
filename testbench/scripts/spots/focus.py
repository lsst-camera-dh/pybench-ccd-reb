
import time
import datetime
import numpy as np
import pyfits

def focus(bench, xyz, exposuretime=5.0,
          zmin=100.0, zmax=101.7, dz=0.001, rep=1, channels=[12]):

    print "Starting a focus with the spot..."

    for z in np.arange(zmin, zmax, dz):
        xyz.move({'z': float(z)})
        pos = xyz.get_position()
        print "Taking %d frame(s) at position... " % rep, pos

        for r in xrange(rep):
            bench.execute_sequence('Acquisition',
                                   exposuretime=exposuretime)
            time.sleep(5)
            d = datetime.date.today().isoformat().replace('-','')
            fitsname = ( '/home/lsst/test_frames/%s/' % d ) + bench.primeheader['IMAGETAG'] + '.fits'
            hdulist = pyfits.open(fitsname, mode = 'update')
            hdulist[0].header['XYZ_X'] = pos['x']
            hdulist[0].header['XYZ_Y'] = pos['y']
            hdulist[0].header['XYZ_Z'] = pos['z']
            # keep only specified channels (12 -> CHAN_12)
            allchannels = range(16)
            tokeep = channels
            for ch in allchannels:
                if ch in tokeep:
                    continue
                key = 'CHAN_%d' % ch
                try:
                    del hdulist[key]
                except KeyError:
                    pass

            hdulist.writeto(fitsname, clobber=True)
                
        
    print "Focusing of the spot done."
    


