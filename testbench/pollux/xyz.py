#! /usr/bin/env python
#
# ==================================================================
#
# LSST
#
# High level control of the XYZ used on the LSST testbench
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
    default_x_port = "/dev/ttyUSB0"
    default_y_port = "/dev/ttyUSB1"
    default_z_port = "/dev/ttyUSB2"

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 x_port = default_x_port,
                 y_port = default_y_port,
                 z_port = default_z_port,
                 debug = True):

        self.x_port = x_port
        self.y_port = y_port
        self.z_port = z_port

        self.x_axis = None
        self.y_axis = None
        self.z_axis = None

        self.debug = debug

    # ---------- Open the various devices --------------------

    def open(self):
        """
        Open the three devices.
        """

        # ------- X Axis --------------------------------------------------

        if (self.x_port != None):
            if self.debug: print >>sys.stderr,  ( "Opening X axis %s ..." % 
                                                  self.x_port )
            self.x_axis = pollux.Pollux(port = self.x_port,
                                        debug = self.debug)
            self.x_axis.open()
            if self.debug: print >>sys.stderr,  ( "Opening X axis %s done." % 
                                                  self.x_port )
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        # ------- Y Axis --------------------------------------------------

        if (self.y_port != None):
            if self.debug: print >>sys.stderr,  ( "Opening Y axis %s ..." % 
                                                  self.y_port )
            self.y_axis = pollux.Pollux(port = self.y_port,
                                        debug = self.debug)
            self.y_axis.open()
            if self.debug: print >>sys.stderr,  ( "Opening Y axis %s done." % 
                                                  self.y_port )
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."

        # ------- Z Axis --------------------------------------------------

        if (self.z_port != None):
            if self.debug: print >>sys.stderr,  ( "Opening Z axis %s ..." % 
                                                  self.z_port )
            self.z_axis = pollux.Pollux(port = self.z_port,
                                        debug = self.debug)
            self.z_axis.open()
            if self.debug: print >>sys.stderr,  ( "Opening Z axis %s done." % 
                                                  self.z_port )
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."


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
        if (self.x_axis != None):
            self.x_axis.home()
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        if (self.y_axis != None):
            self.y_axis.home()
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."

        if (self.z_axis != None):
            self.z_axis.home()
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."

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
