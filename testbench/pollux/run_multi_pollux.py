#! /usr/bin/env python

# ==================================================================
#
# To handle several pollux motors at the same time (axis x,y,z)
#
# Author: Remy Le Breton
#
# ==================================================================

import pollux as p  

#Attention au nom des peripheriques

x = p.Pollux_motor(port = "/dev/ttyUSB2")
y = p.Pollux_motor(port = "/dev/ttyUSB3")
#z = p.Pollux_motor(port = "/dev/ttyUSB2")

#Open the axis

x.open()
y.open()
#z.open()

#Initialize the axis:
#Define the zero position and the range for each axis

limits_x = x.find_limits()
limits_y = y.find_limits()
#limits_z = z.find_limits()

#Functions to handle moving several axis in absolute
#and relative way.

def move_abs_axis(pos_x, pos_y, pos_z, check = False):
    """
    Take the position in mm to absolute move to for each axis.
    Example : move at the 5 mm coordinate over axis x : move_axis(5,0,0)

    @param pos_x: coordinate to move to on the x axis

    @param pos_y: see pos_x

    @param pos_z: see pos_x

    @param check: to take into account the limits of the range
    """

    x.move_absolute(pos_x, check)
    y.move_absolute(pos_y, check)
    #z.move_absolute(pos_z, check)

def move_rel_axis(mm_x, mm_y, mm_z, check = False):
    """
    Take the position in mm to relatively move to for each axis.
    Example1 : move of 5 mm from the actual position along axis x : move_axis(5,0,0)
    Example1 : move of -10 mm from the actual position along axis y : move_axis(0,-10,0)

    @param mm_x: coordinate to move to on the x axis

    @param mm_y: see mm_x

    @param mm_z: see mm_x

    @param check: to take into account the limits of the range
    """

    x.move_relative(mm_x)
    y.move_relative(mm_y)
    #z.move_relative(mm_z)


#Positioning in the center of each axis before beginning the experiment

move_abs_axis(limits_x['up']/2., limits_y['up']/2., 0) #Changer la valeur par defaut de z en "limits_y['up']/2.".

pos_ini_x = x.get_position()
pos_ini_y = y.get_position()
#pos_ini_z = z.get_position()

#Then chose the positions you want to go to...
