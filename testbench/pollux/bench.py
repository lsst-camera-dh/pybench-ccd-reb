#! /usr/bin/env python
#
# ==================================================================
#
# SkyDice
#
# High level control of the SkyDice testbench
#
# Authors: Laurent Le Guillou & Pier-Francesco Rocci
#
# ==================================================================

import sys
import os, os.path
import time

import microlynx_z as mlz
import mdrive_xy as mdxy

# ============ Bench Controller ====================================

class Bench(object):
    """
    High level class representing the bench motors
    """
    default_source_xy_port = "/dev/ttyUSB-MD-CC200-000"
    default_sensor_xy_port = "/dev/ttyS1"
    default_sensor_z_port  = "/dev/ttyS2"

    source_xy_mm = 12800.0 # steps / mm
    sensor_xy_mm = 12800.0 # steps / mm
    sensor_z_mm  =  2560.0 # steps / mm

    allowed_units = ["mm", "step"]

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 source_xy_port = default_source_xy_port,
                 sensor_xy_port = default_sensor_xy_port,
                 sensor_z_port  = default_sensor_z_port,
                 debug = True):

        self.source_xy_port = source_xy_port
        self.sensor_xy_port = sensor_xy_port
        self.sensor_z_port  = sensor_z_port

        self.source_xy_axis = None
        self.sensor_xy_axis = None
        self.sensor_z_axis  = None

        self.sensor_axes_names = {'X' : 'H', 'H' : 'H',
                                  'Y' : 'V', 'V' : 'V',
                                  'Z' : 'Z'}
        self.sensor_axes = self.sensor_axes_names.keys()

        self.source_axes_names = {'X' : 'H', 'H' : 'H',
                                  'Y' : 'V', 'V' : 'V'}
        self.source_axes = self.source_axes_names.keys()

        self.debug = debug

    # ---------- Translate axes names (and check it) ---------

    def _sensor_get_axis(self, axis):
        _axis = axis.upper()

        if _axis not in self.sensor_axes:
            raise ValueError("Undefined sensor axis %s" % axis) 

        return self.sensor_axes_names[_axis]


    def _source_get_axis(self, axis):
        _axis = axis.upper()

        if _axis not in self.source_axes:
            raise ValueError("Undefined source axis %s" % axis) 

        return self.source_axes_names[_axis]


    # ---------- Open the various devices --------------------

    def open(self):
        """
        Open the three devices.
        """
        if (self.source_xy_port != None):
            if self.debug: print >>sys.stderr,  ("Opening source XY axes %s ..." % 
                                  self.source_xy_port)
            self.source_xy_axis = mdxy.MDrive_XY(port = self.source_xy_port,
                                                 debug = self.debug)
            self.source_xy_axis.open()
            if self.debug: print >>sys.stderr,  ("Opening source XY axes %s done." % 
                                  self.source_xy_port)
        else:
            if self.debug: 
                print >>sys.stderr,  "Source XY axes disabled."


        if (self.sensor_z_port != None):
            if self.debug: print >>sys.stderr,  ("Opening sensor Z axis %s ..." % 
                                  self.sensor_z_port)
            self.sensor_z_axis = mlz.MDrive_Z(port = self.sensor_z_port,
                                              debug = self.debug)
            self.sensor_z_axis.open()
            if self.debug: print >>sys.stderr,  ("Opening sensor Z axis %s done." % 
                                  self.sensor_z_port)
        else:
            if self.debug: 
                print >>sys.stderr,  "Sensor Z axis disabled."

        if (self.sensor_xy_port != None):
            if self.debug: print >>sys.stderr,  ("Opening sensor XY axes %s ..." % 
                                  self.sensor_xy_port)
            self.sensor_xy_axis = mdxy.MDrive_XY(port = self.sensor_xy_port,
                                                 debug = self.debug)
            self.sensor_xy_axis.open()
            if self.debug: print >>sys.stderr,  ("Opening sensor XY axes %s done." % 
                                  self.sensor_xy_port)
        else:
            if self.debug: 
                print >>sys.stderr,  "Sensor XY axes disabled."

    # ---------- Close the three devices --------------------- 

    def close(self):
        """
        Close the three devices.
        """ 
        if (self.source_xy_axis != None):
            self.source_xy_axis.close()

        if (self.sensor_xy_axis != None):
            self.sensor_xy_axis.close()

        if (self.sensor_z_axis != None):
            self.sensor_z_axis.close()

            
    # ---------- Setup the motors -----------------------------

    def setup(self, minimal = False):
        """
        Initialize each connected motor (init strings).
        """
        if (self.source_xy_axis != None):
            self.source_xy_axis.setup(minimal)
        else:
            if self.debug: 
                print >>sys.stderr,  "Source XY axes disabled."

        if (self.sensor_xy_axis != None):
            self.sensor_xy_axis.setup(minimal)
        else:
            if self.debug: 
                print >>sys.stderr,  "Sensor XY axes disabled."

        if (self.sensor_z_axis != None):
            self.sensor_z_axis.setup(minimal)
        else:
            if self.debug: 
                print >>sys.stderr,  "Sensor Z axis disabled."


    # ---------- Current motor position ---------------------- 

    def sensor_position(self, unit = "step"):
        x = self.sensor_get_position('X', unit)
        y = self.sensor_get_position('Y', unit)
        z = self.sensor_get_position('Z', unit)
        return x,y,z

    def sensor_get_position(self, axis, unit = "step"):
        """
        Return the current sensor position on axis 'axis'.
        """

        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")
        
        _axis = self._sensor_get_axis(axis)

        position = None
        converted_position = None

        if _axis in ['X','Y','H','V']:
            if (self.sensor_xy_axis != None):
                position = self.sensor_xy_axis.get_position(_axis)
                converted_position = position
                if (position != None) and (unit == "mm"):
                        converted_position = position / self.sensor_xy_mm
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor XY axes disabled."

        elif _axis in ['Z']:
            if (self.sensor_z_axis != None):
                position = self.sensor_z_axis.get_position()
                converted_position = position
                if (position != None) and (unit == "mm"):
                        converted_position = position / self.sensor_z_mm
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor Z axis disabled."

        return converted_position


    def source_position(self, unit = "step"):
        x = self.source_get_position('X', unit)
        y = self.source_get_position('Y', unit)
        return x,y

    def source_get_position(self, axis, unit = "step"):
        """
        Return the current source position on axis 'axis'.
        """

        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")

        _axis = self._sensor_get_axis(axis)

        position = None
        converted_position = None

        if (self.source_xy_axis != None):
            position = self.source_xy_axis.get_position(_axis)
            converted_position = position
            if (position != None) and (unit == "mm"):
                converted_position = position / self.source_xy_mm

        return converted_position


    # ---------- Move absolute and relative ------------------ 

    def sensor_move_absolute(self, axis, position, unit = "step"):
        """
        Move the sensor axis 'axis' to absolute position 'position'.
        @param position: target position.
        """
        
        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")

        _axis = self._sensor_get_axis(axis)

        if _axis in ['X','Y','H','V']:
            if (self.sensor_xy_axis != None):
                step_position = position
                if unit == "mm":
                    step_position = position * self.sensor_xy_mm
                self.sensor_xy_axis.move_absolute(_axis, step_position)
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor XY axes disabled."

        elif _axis in ['Z']:
            if (self.sensor_z_axis != None):
                step_position = position
                if unit == "mm":
                    step_position = position * self.sensor_z_mm
                self.sensor_z_axis.move_absolute(step_position)
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor Z axis disabled."


    def sensor_move_relative(self, axis, offset, unit = "step"):
        """
        Move the sensor axis 'axis' of relative offset 'offset'.
        @param offset: position offset (positive or negative)
        """

        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")

        _axis = self._sensor_get_axis(axis)

        if _axis in ['X','Y','H','V']:
            if (self.sensor_xy_axis != None):
                step_offset = offset
                if unit == "mm":
                    step_offset = offset * self.sensor_xy_mm
                self.sensor_xy_axis.move_relative(_axis, step_offset)
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor XY axes disabled."

        elif _axis in ['Z']: 
            if (self.sensor_z_axis != None):
                step_offset = offset
                if unit == "mm":
                    step_offset = offset * self.sensor_z_mm
                self.sensor_z_axis.move_relative(step_offset)
            else:
                if self.debug: 
                    print >>sys.stderr,  "Sensor Z axis disabled."


    def source_move_absolute(self, axis, position, unit = "step"):
        """
        Move the source axis 'axis' to absolute position 'position'.
        @param position: target position.
        """

        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")

        _axis = self._source_get_axis(axis)

        if (self.source_xy_axis != None):
            step_position = position
            if unit == "mm":
                step_position = position * self.source_xy_mm
            self.source_xy_axis.move_absolute(_axis, step_position)
        else:
            if self.debug: 
                print >>sys.stderr,  "Source XY axes disabled."


    def source_move_relative(self, axis, offset, unit = "step"):
        """
        Move the source axis 'axis' of relative offset 'offset'.
        @param offset: position offset (positive or negative)
        """

        if unit not in self.allowed_units:
            raise ValueError("Invalid unit: unit should be either step or mm")

        _axis = self._source_get_axis(axis)

        if (self.source_xy_axis != None):
            step_offset = offset
            if unit == "mm":
                step_offset = offset * self.source_xy_mm
            self.source_xy_axis.move_relative(_axis, step_offset)
        else:
            if self.debug: 
                print >>sys.stderr,  "Source XY axes disabled."


# ==================================================================
