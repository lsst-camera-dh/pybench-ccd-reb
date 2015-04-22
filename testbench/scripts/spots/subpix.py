
import time
import numpy as np
import pyfits

def subpix(bench, xyz, exposuretime=5.0,
           dx=0.001, dy=0.001, nx=20, ny=20, rep=2):

    print "Starting subpixel imaging of the spot..."

    for ix in np.arange(0.0, (nx+1)*dx, dx):
        for iy in np.arange(0.0, (ny+1)*dy, dy):

            pos = xyz.get_position()
            print "Taking %d frame(s) at position... " % rep, pos

            for r in xrange(rep):
                bench.execute_sequence('Acquisition',
                                       exposuretime=exposuretime)
                time.sleep(5)
                fitsname = '/home/lsst/test_frames/20141008/' + bench.primeheader['IMAGETAG'] + '.fits'
                hdulist = pyfits.open(fitsname, mode = 'update')
                hdulist[0].header['XYZ_X'] = pos['x']
                hdulist[0].header['XYZ_Y'] = pos['y']
                hdulist[0].header['XYZ_Z'] = pos['z']
                # keep only CHAN_12
                for ext in [0,1,2,3,4,5,6,7,8,9,10,11,13,14,15]:
                    k = 'CHAN_%d' % ext
                    try:
                        del hdulist[k]
                    except KeyError:
                        pass

                hdulist.writeto(fitsname, clobber=True)
                
            xyz.move({'dy': dy})

        xyz.move({'dx': dx})
        
    print "Subpixel imaging of the spot done."
    


