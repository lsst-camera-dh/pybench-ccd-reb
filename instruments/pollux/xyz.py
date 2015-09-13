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

    # default_ports = { 'x': "/dev/ttyS16",
    #                   'y': "/dev/ttyS17",
    #                   'z': "/dev/ttyS18" }

    default_ports =    { 'x': "/dev/ttyS16",
                         'y': "/dev/ttyS16",
                         'z': "/dev/ttyS16",
                         'a': "/dev/ttyS16" }

    default_serials =  { 'x':  '9050719',
                         'y': '10050833',
                         'z':  '9050809',
                         'a': '15051379' }

    default_axis_ids = { 'x': 1,
                         'y': 2,
                         'z': 3,
                         'a': 4 }

    # ---------- Constructor ---------------------------------

    def __init__(self,
                 ports = default_ports, 
                 serials = default_serials,
                 axis_ids = default_axis_ids,
                 debug = True):

        self.ports = ports
        self.serials = serials
        self.axis_ids = axis_ids

        self.axes = { 'x': None, 
                      'y': None, 
                      'z': None, 
                      'a': None }

        self.homed = False

        self.debug = debug

    # ---------- Open the various devices --------------------

    def open(self, check = True):
        """
        Open all the connected devices, and checking serial numbers
        and axis_id to avoid misidentification of axes.

        Axis A (4) (angle) is optional. Everything should work
        even if it is missing.
        """

        # -- Firt open X axis --------------------------------

        for ax in ['x', 'y', 'z', 'a']:

            if ( not(self.ports.has_key(ax)) or
                 not(self.serials.has_key(ax)) or
                 not(self.axis_ids.has_key(ax)) ): continue

            if self.debug: 
                print >>sys.stderr, ( "Opening '%s' axis on port %s ..." % 
                                      (ax, self.ports[ax]) )
            # Opening the Axis

            axis = pollux.Pollux(port = self.ports[ax],
                                 axis_id = self.axis_ids[ax],
                                 debug = self.debug)
            try: 
                axis.open()
            except IOError:
                if self.debug: 
                    print >>sys.stderr, ( "No axis '%s' on port %s." % 
                                          ( ax, self.ports[ax] ) )
                continue
                    

            if self.debug: 
                print >>sys.stderr, ( "Opening axis '%s' on port %s done." % 
                                      ( ax, self.ports[ax] ) )

            motor_serial = axis.get_serial()
            # print repr(motor_serial)

            if motor_serial != self.serials[ax]:
                raise IOError("Wrong Axis (wrong/unknown serial number)")

            self.axes[ax] = axis

        # --

        if check:
            if self.axes['x'] == None:
                raise IOError("Missing X Axis")

            if self.axes['y'] == None:
                raise IOError("Missing Y Axis")

            if self.axes['z'] == None:
                raise IOError("Missing Z Axis")

        # No check for optional A axis.


    # ---------- Close the three/four devices ----------------

    def close(self):
        """
        Close the three/four devices.
        """ 
        for ax in ['x', 'y', 'z', 'a']:
            if (self.axes[ax] != None):
                self.axes[ax].close()

            
    # ---------- Setup the motors ----------------------------

    def setup(self):
        """
        Initialize each connected motor (init strings).
        """

        for ax in ['x', 'y', 'z', 'a']:
            if (self.axes[ax] != None):
                self.axes[ax].setup()
            else:
                if self.debug: 
                    print >>sys.stderr,  "%s axis disabled." % ax


    # ---------- Home procedure for the motors ---------------

    def home(self, force = False, park = True):
        """
        Find the limits for all motors.
        Then park it.
        """ 

        if self.homed and not(force):
            # put the 3 motors half-range ?
            if park: self.park()
            return

        # To avoid breaking the objective, we first go backward
        # on the z axis, then initialize the x and y axes, and at
        # last detect the forward end position on the z axis.

        # First send the Z motor backward
        self.axes['z'].find_limits(lower=True, upper=False)

        # Then find the limits for X and Y axes
        # and put the motor half range (critical)
        self.axes['x'].home()
        self.axes['y'].home()

        # at last init of z axis (find limits and put motor half range)
        self.axes['z'].home()

        # If axis A is present, homing (take a lot of time)
        if (self.axes['a'] != None):
            self.axes['a'].home()
            
        # then park it
        if park: self.park()

        self.homed = True


    # ---------- Park position -------------------------------


    def park(self):
        """
        Park the XYZ(A) out of the light beam.
        Even if no homing has been done, parking should work properly.
        """ 

        # Even if no homing has been done, parking is OK

        if ( (self.axes['x'] == None) or 
             (self.axes['y'] == None) or 
             (self.axes['z'] == None) ):
            # cannot park safely
            raise pollux.MotorError("Some axes are missing (have you done a 'open' first): cannot park safely.")

        # min pos for z axis first
        self.axes['z'].find_limits(upper = False, lower = True)
        self.move(dz = +1.0) # to avoid blocking the motor

        # Then, max pos for x and y axes
        self.axes['x'].find_limits(upper = True, lower = False)
        self.move(dx = -1.0) # to avoid blocking the motor

        self.axes['y'].find_limits(upper = True, lower = False)
        self.move(dy = -1.0) # to avoid blocking the motor

        # Then, zero pos for a axis
        if (self.axes['a'] != None):
            self.axes['a'].move_absolute(0.0)


    # ---------- Current motor position ---------------------- 

    def get_position(self):
        """
        Return the current position on the XYZ(A) motors 
        (as a dictionary).
        It is then possible to do move(**get_position())
        """

        position = {}

        if (self.axes['x'] != None):
            position['x'] = self.axes['x'].get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        if (self.axes['y'] != None):
            position['y'] = self.axes['y'].get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."

        if (self.axes['z'] != None):
            position['z'] = self.axes['z'].get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."

        if (self.axes['a'] != None):
            position['a'] = self.axes['a'].get_position()
        else:
            if self.debug: 
                print >>sys.stderr,  "A axis disabled."

        return dict(position)


    position = property(get_position, doc = "XYZ(A) current position")

    # ---------- Compute the target position -----------------

    def compute_target(self,
                       x  = None, y  = None, z  = None,
                       dx = None, dy = None, dz = None):

        pos = self.get_position()
        xc = pos['x']
        yc = pos['y']
        zc = pos['z']

        xt, yt, zt = xc, yc, zc
        
        if x != None:  xt = x
        if dx != None: xt += dx
        
        if y != None:  yt = y
        if dy != None: yt += dy
        
        if z != None:  zt = z
        if dz != None: zt += dz
        
        return xt, yt, zt

    # ---------- Check if a given position is allowed --------

    def check_target(self, x, y, z):
        """
        Check the target position.
        Permitted volume for the 2 "grey cryostat"
        -- LLG, RLB, SK - 20150504
        """

        if (x < 0.0) or (x > 101.7):
            raise ValueError("XYZ coordinate x out of allowed range.")

        if (y < 0.0) or (y > 101.7):
            raise ValueError("XYZ coordinate y out of allowed range.")

        if (z < 0.0) or (z > 101.7):
            raise ValueError("XYZ coordinate z out of allowed range.")

        # Extra restriction to avoid crashing against the wall ;-)
        # ----------------------------------------------------------------
        # Grey cryostats, new settings

        xcenter = 41.60
        ycenter = 38.42
        radius = 22.5
        zwall = 72.0

        if z > zwall:
            dist = ( (x-xcenter)**2 + (y-ycenter)**2 )**.5
            if dist > radius:
                raise ValueError(
                    "XYZ target not allowed: will hit the window mount!!!")

        #----------------------------------------------------------------
        # # Former: orange cryostat
        # xcenter = 33.42
        # ycenter = 44.52
        # radius = 24.0
        # zwall = 81.8
        #----------------------------------------------------------------

        return True


    # ---------- Move absolute and relative ------------------ 

    def move(self, 
             x  = None, y  = None, z  = None, a = None,
             dx = None, dy = None, dz = None, da = None,
             wait = True, check = True):
        """
        Move the XYZ(A) to the given position (or offset).
        This function can do relative and absolute movements.
        """

        ## First, check the geometric limits
        #
        # Due to the complicated shape of the permitted volume,
        # the limits *MUST* be checked before and after each 
        # independant movement.
        # Reason: it may happen that the target is allowed, 
        # but the separate movements to go there are not!!!

        # -------- X axis ------------------------------------

        if (self.axes['x'] != None):

            if x != None:
                if check:
                    xt, yt, zt = self.compute_target(x=x)
                    self.check_target(xt, yt, zt)

                self.axes['x'].move_absolute(position = x,  
                                             wait = wait, check = check)

            if dx != None:

                if check:
                    xt, yt, zt = self.compute_target(dx=dx)
                    self.check_target(xt, yt, zt)

                self.axes['x'].move_relative(offset = dx, 
                                             wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "X axis disabled."

        # -------- Y axis ------------------------------------

        if (self.axes['y'] != None):

            if y != None:

                if check:
                    xt, yt, zt = self.compute_target(y=y)
                    self.check_target(xt, yt, zt)

                self.axes['y'].move_absolute(position = y,  
                                             wait = wait, check = check)

            if dy != None:

                if check:
                    xt, yt, zt = self.compute_target(dy=dy)
                    self.check_target(xt, yt, zt)

                self.axes['y'].move_relative(offset = dy, 
                                             wait = wait, check = check)

        else:
            if self.debug: 
                print >>sys.stderr,  "Y axis disabled."


        # -------- Z axis ------------------------------------

        if (self.axes['z'] != None):

            if z != None:

                if check:
                    xt, yt, zt = self.compute_target(z=z)
                    self.check_target(xt, yt, zt)

                self.axes['z'].move_absolute(position = z,  
                                             wait = wait, check = check)

            if dz != None:

                if check:
                    xt, yt, zt = self.compute_target(dz=dz)
                    self.check_target(xt, yt, zt)

                self.axes['z'].move_relative(offset = dz, 
                                             wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "Z axis disabled."

        # -------- A axis ------------------------------------

        if (self.axes['a'] != None):

            if a != None:
                self.axes['a'].move_absolute(position = a,  
                                             wait = wait, check = check)

            if da != None:
                self.axes['a'].move_relative(offset = da, 
                                             wait = wait, check = check)
        else:
            if self.debug: 
                print >>sys.stderr,  "A axis disabled."


# ==================================================================
