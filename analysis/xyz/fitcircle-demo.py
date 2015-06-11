#! /usr/bin/env python

# Author: Laurent Le Guillou
# Algorithm from: http://www.math.niu.edu/~rusin/known-math/96/circle.fit
# ('more elegant approach', la seconde méthode)

import sys
import os, os.path

import numpy as np
import numpy.linalg as la
import pylab as pb

# Generate points (random points on a given circle, with some noise)

R  = 65.2 # mm
X0 = 45.8 # mm
Y0 = 23.4 # mm
n = 8

angles = np.random.uniform(0., 2 * np.pi, size = n)
xs = X0 + R * np.cos(angles) + np.random.normal(0., 1., size = n)
ys = Y0 + R * np.sin(angles) + np.random.normal(0., 1., size = n)

# fitting a circle (minimizing the square of the area difference)
# -> linear problem -> linear least square

xsm = xs[:]
ysm = ys[:]
xsm.shape = (n,1)
ysm.shape = (n,1)
M = np.hstack([xsm,ysm,np.ones(shape = (n,1))])
B = - xs**2 - ys**2
B.shape = (n,1)

X, residuals, rank, s = la.lstsq(M, B)

x0 = -X[0,0]/2.
y0 = -X[1,0]/2.
r = (x0**2 + y0**2 - X[2,0])**.5

print "Simulated : ", "center = (%f,%f)  radius = %f" % (X0, Y0, R)
print "Fitted    : ", "center = (%f,%f)  radius = %f" % (x0, y0, r)


# plotting the result (the best fit circle)

phis = np.arange(0, 2*np.pi, .01)
xf = x0 + r*np.cos(phis)
yf = y0 + r*np.sin(phis)


pb.cla()
pb.scatter(xs, ys, marker = '+', color = 'black')
# pb.scatter(xf, yf, marker = '.', s = 0.1, color = 'red')
pb.plot(xf, yf, 'r-')
pb.axes().set_aspect('equal')
pb.show()



