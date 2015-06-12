
import numpy as np
from scipy.optimize import curve_fit



def func(x, A,B,x1,x2,a1,a2):
    return A*.25*(1+np.tanh(a1*(x-x1)))*(1-np.tanh(a2*(x-x2))) + B


flux = np.loadtxt("shutter-clap-laser-0001-first-pulse.data")
time = np.arange(len(flux))

A=-120.
B=5
x1=68000.
x2=85000.
a1=0.1
a2=0.1
p0 = [A,B,x1,x2,a1,a2]



popt, pcov = curve_fit(func, time, flux, p0=p0)
print popt

A,B,x1,x2,a1,a2 = popt

residuals = flux - func(time,A,B,x1,x2,a1,a2)
# error ??
chi2 = (residuals**2).sum()
dof = len(flux) - 6
chi2dof = chi2/dof

print chi2, dof, chi2dof

import pylab as pb

pb.figure(1)
pb.scatter(time, flux, marker='+', color='black')
pb.plot(time, func(time,A,B,x1,x2,a1,a2), color='red')

pb.figure(2)
pb.scatter(time, flux -  func(time,A,B,x1,x2,a1,a2), marker='+', color='black')
pb.plot(time, np.zeros(shape=(len(time),)), color='red')



from peakdetect import *


def analyze(fluxes):
    ys,xs = np.histogram(fluxes, bins=50)
    centers = (xs[1:] + xs[:-1])/2.
    uppeaks,downpeaks = peakdetect(ys, centers, lookahead=1)
    print uppeaks
    peakcmp = lambda x,y: cmp(y[1],x[1])
    uppeaks.sort(cmp = peakcmp)

    # Take the 2 biggest peaks
    print uppeaks
    if len(uppeaks) < 2:
        raise RuntimeError("Cannot find 2 peaks")

    xpeaks,effpeaks = zip(*(uppeaks[:2]))
    print uppeaks[:2]
    print xpeaks,effpeaks
    xpeaks = list(xpeaks)
    xpeaks.sort()
    print xpeaks

    B0 = xpeaks[1]
    A0 = xpeaks[0] - B0

