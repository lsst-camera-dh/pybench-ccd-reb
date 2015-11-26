#! /usr/bin/env python 

# ds9display.py : operate a ds9 window to display images
# original class by Peter Doherty

import pyds9
import logging
import os


class ds9display(object):
    def __init__(self, name):
        self.__name = name
        self.__disp = pyds9.DS9(start=True, wait=100, verify=True)
        self.cmap = 'grey'
        self.__disp.set("cmap %s" % self.cmap)
        self.__disp.set("view object no")
        self.__disp.set("zoom to fit")
        self.__disp.set("view wcs no")

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

    def load_file(self, file):
        if (os.path.isfile(file) == True):
            err = self.set("file mosaicimage iraf %s" % file, verbose=False)

    def load_array(self, a, verbose=False):
        err = self.__disp.set_np2arr(a)
        if (err == 0):
            logging.error("IMDISP: Error loading array")
        else:
            if (verbose == True):
                logging.info("IMDISP: loaded from array")
        return err

    def load_hdulist(self, h, verbose=False):
        err = self.__disp.set_pyfits(h)
        if (err == 0):
            logging.error("IMDISP: Error loading HDU list")
        else:
            if (verbose == True):
                logging.info("IMDISP: loaded from HDU list")
        return err

    def scale(self, type):
        if type in ['linear', 'log', 'power', 'sqrt', 'squared', 'asinh', 'histogram', 'minmax', 'zscale']:
            err = self.set("scale %s" % type, verbose=False)
