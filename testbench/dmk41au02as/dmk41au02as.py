#! /usr/bin/env python
#
# Author: Laurent Le Guillou
#

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits


class Camera(object):
    """
    A minimal class to interact with a DML41AU02.AS USB camera.

    Example of use:

      cam = Camera()
      cam.open()
      img = cam.capture(exposure = 2.0e-1) 
      cam.close()
      data = np.array(img)
      fits = pyfits.PrimaryHDU()
      fits.data = data
      fits.writeto("test.fits", clobber=True)


    """

    def __init__(self):
        self.device = None
        self.default_expo_int = 333 # * 1.0e-4 s

    def open(self):
        """
        Find if a DML41AU02.AS USB camera is connected and set it up.
        """
        devices = unicap.enumerate_devices()
        print devices

        if len(devices) == 0:
            # No device managed by Unicap connected
            raise IOError("No Unicap managed device connected.")

        # Looking for the camera in the device list
        
        # To implement

        # Open it
        self.device = unicap.Device( unicap.enumerate_devices()[1] ) # to change

        # Set it up

        # Get a list of supported video formats
        self.fmts = self.device.enumerate_formats()

        # Set the first video format in the list at maximum resolution
        self.fmt = self.fmts[0]
        self.fmt['size'] = self.fmt['max_size']
        self.device.set_format(self.fmt)

        # set the exposure time mode
        auto_exposure_mode = self.device.get_property({'identifier': 'Exposure, Auto'})
        self.device.set_property({'identifier': 'Exposure, Auto', 'value': 1})

        # exposure = int(self.device.get_property({'identifier': 'Exposure (Absolute)'}))
        self.device.set_property({'identifier': 'Exposure (Absolute)', 'value': self.default_expo_int})


    def capture(self, exposure = 1.0e-2):
        """
        Take one shot with exposure <exposure> (in seconds).
        Return a PIL image object.
        """
        expo_int = int(exposure / 1e-4)

        # TODO : check if the value is allowed

        auto_exposure_mode = self.device.get_property({'identifier': 'Exposure, Auto'})
        self.device.set_property({'identifier': 'Exposure, Auto', 'value': 1})

        # exposure = int(self.device.get_property({'identifier': 'Exposure (Absolute)'}))
        self.device.set_property({'identifier': 'Exposure (Absolute)', 'value': expo_int})

        # Start capturing video
        self.device.start_capture()

        # wait for the exposure to be finished (with some overhead time)
        time.sleep(1.2 * exposure)

        # Capture an image
        imgbuf = self.device.wait_buffer()

        print >>sys.stderr, \
            ( 'Captured an image. Colorspace: ' + str( imgbuf.format['fourcc'] ) \
                  + ', Size: ' + str( imgbuf.format['size'] ) )

        # Convert the image to RGB3
        # rgbbuf = imgbuf.convert( 'RGB3' )
        # rgbbuf = buf.convert( 'RGB3' )

        img = Image.fromstring( 'L', 
                                imgbuf.format['size'], 
                                imgbuf.tostring() )

        self.device.stop_capture()

        return img


    def capture_and_save(self, exposure, filename, filetype):
        """
        Take one shot with exposure <exposure> (in seconds).
        Save the resulting image to file <filename>.
        """

        img = self.capture(exposure)

        if filetype == "FITS":
            data = np.array(img)
            # print data.min(), data.max()
            fits = pyfits.PrimaryHDU()
            fits.data = data
            fits.writeto("%s.fits" % filename, clobber=True)
        else:
            img.save("%s.%s" % (filename, filetype.lower()), filetype)


    def close(self):
        pass
