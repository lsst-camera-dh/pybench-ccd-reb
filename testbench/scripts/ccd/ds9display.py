#! /usr/bin/env python 

# ds9display.py : operate a ds9 window to display images
# original class by Peter Doherty

# TODO: move to a driver

import pyds9
import logging
import astropy.io.fits as pyfits

import lsst.testbench.bench as bench

class DS9display(object):
    def __init__(self, name):
        self.__name = name
        self.__disp = pyds9.DS9(start=True, wait=100, verify=True)
        self.colormap('grey')
        self.set("view object no")
        self.set("view wcs no")
        self.horizontal_graph()
        self.vertical_graph()

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

    def load_file(self, file):
        #if (os.path.isfile(file) == True):
        #    err = self.set("file mosaicimage iraf %s" % file, verbose=False)
        #    self.set("zoom to fit")

        # to bypass bug in vertical and horizontal graphs
        f = pyfits.open(file)
        # TODO: recreate array

        f.close()

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
        err = self.__disp.set_pyfits(h)
        if (err == 0):
            logging.error("IMDISP: Error loading HDU list")
        else:
            if (verbose == True):
                logging.info("IMDISP: loaded from HDU list")
            self.set("zoom to fit")
        return err

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


# could also attach functions for fits files and arrays

def display_hdu(self, hdulist)

    d = DS9display('DS9')
    d.load_hdulist(hdulist)
    d.set_crosshair(100, 100)
    d.scale('minmax')

bench.Bench.display_hdu = display_hdu

