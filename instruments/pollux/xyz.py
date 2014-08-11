#! /usr/bin/env python
#
# ==================================================================
#
# LSST
#
# High level control of the XYZ used on the LSST testbench
# Tuned for the spot projector
#
# Authors: Laurent Le Guillou 
#
# ==================================================================

import sys
import os, os.path
import time

import pollux 

# ============ XYZ control =========================================

class XYZ(object):
    """
    High level class representing the XYZ motorized support.
    """
    default_x_port = "/dev/ttyUSB8"
    default_y_port = "/dev/ttyUSB10"
    default_z_port = "/dev/ttyUSB9"

    default_x_serial =  '9050719'
    default_y_serial = '10050833'
    default_z_serial =  '9050809'

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 ports = [ default_x_port, 
                           default_y_port, 
                           default_z_port ],
                 x_serial = default_x_serial,
                 y_serial = default_y_serial,
                 z_serial = default_z_serial,
                 debug = True):

        self.ports = ports

        self.x_serial = x_serial
        self.y_serial = y_serial
        self.z_serial = z_serial

        self.x_axis = None
        self.y_axis = None
        self.z_axis = None

        self.debug = debug

    # ---------- Open the various devices --------------------

    def open(self, check = True):
        """
        Open the three devices, and checking serial numbers
        to avoid errors.
        """

        for port in self.ports:

            if self.debug: 
                print >>sys.stderr, "Opening axis on port %s ..." % port 

            axis = pollux.Pollux(port = port,
                                 debug = self.debug)
            axis.open()
            if self.debug: 
                print >>sys.stderr, "Opening axis on port %s done." % port 

            motor_serial = axis.get_serial()
            # print repr(motor_serial)

            if motor_serial == self.x_serial:
                self.x_axis = axis
            elif motor_serial == self.y_serial:
                self.y_axis = axis
            elif motor_serial == self.z_serial:
                self.z_axis = axis
            else:
                raise IOError("Unknown Axis (unknown serial number)")

        if check:
            if self.x_axis == None:
                raise IOError("Missing X Axis")

            if self.y_axis == None:
                raise IOError("Missing Y Axis")

            if self.z_axis == None:
                raise IOError("Missing Z Axis")


    # ---------- Close the three devices --------------------- 

    def close(self):
        """
        Close the three devices.
        """ 
        if (self.x_axis != None):
            self.x_axis.close()

        if (self.y_axis != None):
            self.y_axis.close()

        if (self.z_axis != None):
            self.z_axis.close()

            
    # ---------- Setup the motors ----------------------------

    def setup(self):
        """
        Initialize each connected motor (init strings).
        """
        if (self.x_axis != None):
            self.x_axis.setup()
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        if (self.y_axis != None):
            self.y_axis.setup()
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."

        if (self.z_axis != None):
            self.z_axis.setup()
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."


    # ---------- Home procedure for the motors ---------------

    def home(self):
        """
        Find the limits for all motors 
        and define the zero positions in middle range.
        """ 

        # To avoid breaking the objective, we first go backward
        # on the z axis, then initialize the x and y axes, and at
        # last detect the forward end position on the z axis.

        # First send the Z motor backward
        self.z_axis.find_limits(lower=True, upper=False)

        self.x_axis.home()
        self.y_axis.home()

        # at last init of z axis

        self.z_axis.home()

    # ---------- Park position -------------------------------


    def park(self):
        """
        Park the XYZ out of the light beam.
        """ 

        park_position = {
            'x' : self.x_axis.get_limits()['up']   - 1.0,
            'y' : self.y_axis.get_limits()['up']   - 1.0,
            'z' : self.x_axis.get_limits()['down'] + 1.0 }

        # order is important !!
        self.move(z = park_position['z'])

        self.move(x = park_position['x'])
        self.move(y = park_position['y'])


    # ---------- Current motor position ---------------------- 

    def get_position(self):
        """
        Return the current position on the three motors 
        (as a dictionary).
        It is then possible to do move(**get_position())
        """

        position = {}

        if (self.x_axis != None):
            position['x'] = self.x_axis.get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        if (self.y_axis != None):
            position['y'] = self.y_axis.get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."

        if (self.z_axis != None):
            position['z'] = self.z_axis.get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."

        return dict(position)


    position = property(get_position, doc = "XYZ current position")


    # ---------- Move absolute and relative ------------------ 

    def move(self, 
             x  = None, y  = None, z  = None,
             dx = None, dy = None, dz = None, wait = True, check = True):
        """
        Move the XYZ to the given position (or offset).
        This function can do relative and absolute movements.
        """

        # -------- X axis ------------------------------------

        if (self.x_axis != None):
            if x != None:
                self.x_axis.move_absolute(position = x,  
                                          wait = wait, check = check)
            if dx != None:
                self.x_axis.move_relative(offset = dx, 
                                          wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        # -------- Y axis ------------------------------------

        if (self.y_axis != None):
            if y != None:
                self.y_axis.move_absolute(position = y,  
                                          wait = wait, check = check)
            if dy != None:
                self.y_axis.move_relative(offset = dy, 
                                          wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."


        # -------- Z axis ------------------------------------

        if (self.z_axis != None):
            if z != None:
                self.z_axis.move_absolute(position = z,  
                                          wait = wait, check = check)
            if dz != None:
                self.z_axis.move_relative(offset = dz, 
                                          wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."


# ==================================================================
