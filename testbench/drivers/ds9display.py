#! /usr/bin/env python 

# ds9display.py : operate a ds9 window to display images
# C. Juramy based on an original class by Peter Doherty

from driver import Driver
import pyds9
import logging
import astropy.io.fits as pyfits
import numpy as np


#

def split_slicing(strslice):
    """
    Utility function: parses a string with nD slicing into the slicing indexes.
    Exp: '[x, y]' -> [x, y]
    :type strslice: string
    :type n: int
    :rtype: list
    """
    s = strslice.strip('[]')

    dimlist = s.split(',')
    indexes = []

    for pair in dimlist:
        i1, i2 = pair.split(':')
        indexes.append(int(i1))
        indexes.append(int(i2))

    return indexes

def hdulist_to_array(i):
    """ Recreate the array from the HDUlist
    :type i: pyfits.HDUlist
    :rtype: np.array
    """

    detsize = i[0].header['DETSIZE']
    dimlist = split_slicing(detsize)
    # initialize array with 0 over the whole image
    # order of indexes in FITS headers is reversed from order in numpy
    a = np.zeros((dimlist[3], dimlist[1]), dtype=np.int32)

    # fill with data from the CHAN extensions
    for ihdu in i[1:]:
        if 'CHAN' in ihdu.name:
            # replace with data from  DATASEC in the DETSEC section of the new array
            dsec = split_slicing(ihdu.header['DATASEC'])
            pos = split_slicing(ihdu.header['DETSEC'])
            # indexes are in decreasing order if the image is flipped
            if pos[0] < pos[1]:
                x1 = pos[0]-1
                x2 = pos[1]
                xs = 1
            else:
                x1 = pos[0]-1
                x2 = pos[1]-2
                xs = -1
            if pos[2] < pos[3]:
                y1 = pos[2]-1
                y2 = pos[3]
                ys = 1
            else:
                y1 = pos[2]-1
                y2 = pos[3]-2
                ys = -1
            #print '%d:%d:%d, %d:%d:%d' % (y1, y2, ys, x1, x2, xs)
            # note : this relies on the fact that the line direction is not reversed in the [0,yyy] range
            # otherwise we would need to add more cases
            if x2<0:
                # this makes the high limit default to actual -1 (so we go down to 0), not n-1
                a[y1:y2:ys, x1::xs] = ihdu.data[dsec[2]-1:dsec[3], dsec[0]-1:dsec[1]]
            else:
                a[y1:y2:ys, x1:x2:xs] = ihdu.data[dsec[2]-1:dsec[3], dsec[0]-1:dsec[1]]

    return a

class Instrument(Driver):

    # ===================================================================
    # Generic methods (init, open, etc)
    # ===================================================================

    def __init__(self, identifier, **kargs):
        Driver.__init__(self, identifier, **kargs)

    def open(self):
        """
        Connects to the display.
        """
        if self.display:
            self.__disp = pyds9.DS9(self.display)
        else:
            self.__disp = pyds9.DS9(start=True, wait=100, verify=True)

    def is_connected(self):
        """
        Check if the connection is established with the hardware.
        Returns True if the hardware answers, False otherwise.
        """
        answer = self.checkConnection()

        if answer is None:
            return False

        if answer != 'ds9':
            return False

        return True

    def checkConnection(self):
        """
        Check by getting the version of DS9. Answer is e.g. 'ds9 5.7'.
        Return 'ds9' or None.
        """
        try:
            return self.get('version')[:3]
        except ValueError:
            return None

    def register(self, bench):
        self.open()
        connected = self.is_connected()
        if not connected:
            raise IOError("DS9 display could not be reached")

        self.default_config()

        Driver.register(self, bench)

    def close(self):
        """
        Closes the display.
        """
        self.set('quit')

    # ===================================================================
    #  Instrument specific methods
    # ===================================================================

    # basic access points

    def get(self, param_string):
        value_string = self.__disp.get(param_string)
        return value_string

    def set(self, param_string, verbose=False):
        err = self.__disp.set(param_string)
        if (err == 0):
            logging.error("IMDISP: Error setting %s" % param_string)
        else:
            if (verbose == True):
                logging.info("IMDISP: Set %s" % param_string)
        return err

    # setting display parameters

    def about(self):
        info = self.__disp.get('about')
        print info

    def bg(self, color):
        if color in ['black', 'white', 'red', 'blue', 'yellow', 'green', 'grey']:
            err = self.set("bg %s" % color, verbose=False)

    def colormap(self, cmap):
        if cmap in ['grey', 'a', 'b', 'bb', 'he', 'i8', 'aips0', 'heat', 'cool', 'rainbow']:
            err = self.set("cmap %s" % cmap, verbose=False)

    def scale(self, type):
        if type in ['linear', 'log', 'power', 'sqrt', 'squared', 'asinh', 'histogram', 'minmax', 'zscale']:
            err = self.set("scale %s" % type, verbose=False)

    # loading image data to display

    def load_array(self, a, verbose=False):
        err = self.__disp.set_np2arr(a)
        if (err == 0):
            logging.error("IMDISP: Error loading array")
        else:
            if (verbose == True):
                logging.info("IMDISP: loaded from array")
            self.set("zoom to fit")
        return err

    def load_hdulist(self, h, verbose=False):
        #err = self.__disp.set_pyfits(h)

        # there is a bug for vertical and horizontal graphs with multiple HDUs
        # so instead we recreate a single array and display it
        a = hdulist_to_array(h)

        return self.load_array(a, verbose)

    def load_file(self, fitsfile, verbose=False):
        #if (os.path.isfile(file) == True):
        #    err = self.set("file mosaicimage iraf %s" % file, verbose=False)
        #    self.set("zoom to fit")

        # there is a bug for vertical and horizontal graphs with multiple HDUs
        # so instead we recreate a single array and display it
        i = pyfits.open(fitsfile)

        a = hdulist_to_array(i)

        i.close()

        return self.load_array(a, verbose)

    # getting image data from display

    def get_array(self):
        return self.__disp.get_arr2np()

    def get_hdulist(self):
        return self.__disp.get_pyfits()

    # other display manipulations

    def set_crosshair(self, x, y):
        return self.set('crosshair %d %d physical' % (x, y))

    def get_crosshair(self):
        return self.get('crosshair')

    def horizontal_graph(self, on=True):
        return self.set('view graph horizontal %s' % (on and 'yes' or 'no'))

    def vertical_graph(self, on=True):
        return self.set('view graph vertical %s' % (on and 'yes' or 'no'))

    # grouping a few operations for convenience

    def default_config(self):
        self.colormap(self.cmap)
        self.set("view object no")
        self.set("view wcs no")
        self.horizontal_graph()
        self.vertical_graph()


