#! /usr/bin/env python

import sys
import os, os.path
import time

import unicap
import Image
import numpy as np
import pyfits


filename = "test"
exposure = 333 # expressed in 1e-4 second


if len(sys.argv) > 1:
    filename = sys.argv[1]

if len(sys.argv) > 2:
    exposure = int(sys.argv[2])

# Create a device object with the first video capture device found
dev = unicap.Device( unicap.enumerate_devices()[0] )

# Get a list of supported video formats
fmts = dev.enumerate_formats()

# Set the first video format in the list at maximum resolution
fmt = fmts[0]
fmt['size'] = fmt['max_size']
dev.set_format( fmt )

# Get a list of supported device properties
# The properties in this list are set to their default values
props = dev.enumerate_properties()

# Get the current state of the first property
# prop = dev.get_property( props[0] )

# Set the property ( in this example, we do not change the actual value )
# dev.set_property( prop )

auto_exposure_mode = dev.get_property({'identifier': 'Exposure, Auto'})
dev.set_property({'identifier': 'Exposure, Auto', 'value': 1})

# exposure = int(dev.get_property({'identifier': 'Exposure (Absolute)'}))
dev.set_property({'identifier': 'Exposure (Absolute)', 'value': exposure})


# Start capturing video
dev.start_capture()

time.sleep(2 * exposure * 1.e-4)

# Capture an image
imgbuf = dev.wait_buffer()

print 'Captured an image. Colorspace: ' + str( imgbuf.format['fourcc'] ) + ', Size: ' + str( imgbuf.format['size'] )

# Convert the image to RGB3
# rgbbuf = imgbuf.convert( 'RGB3' )
# rgbbuf = buf.convert( 'RGB3' )

img = Image.fromstring( 'L', 
                        imgbuf.format['size'], 
                        imgbuf.tostring() )

img.save("%s.tiff" % filename, "TIFF")

data = np.array(img)

print data.min(), data.max()

fits = pyfits.PrimaryHDU()
fits.data = data
fits.writeto("%s.fits" % filename, clobber=True)

# Stop capturing video
dev.stop_capture()


