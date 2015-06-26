
import numpy as np
from scipy.optimize import curve_fit

import pylab as pb

def model(x, A,B,x1,x2,a1,a2):
    return A*.25*(1+np.tanh(a1*(x-x1)))*(1-np.tanh(a2*(x-x2))) + B

from peakdetect import *

def lookforswitch(data, threshold, n, start=0, up=True):
    if up: 
        mask = (data > threshold)
    else: 
        mask = (data < threshold)

    mask_str = mask.tostring()

    pattern = np.array(n * [True])
    pattern_str = pattern.tostring()

    idx = mask_str.find(pattern_str, start)

    return idx


def analyse(fluxes):
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
    print B0
    print A0

    # Try to identify the two transitions, in a robust way
    # (to avoid misidentification due to spikes)

    down = lookforswitch(fluxes, (A0+B0)/2.0, n = 3, start = 0, up = False)

    if down == -1:
        down = 0

    up = lookforswitch(fluxes, (A0+B0)/2.0, n = 3, start = down, up = True)

    if up == -1:
        up = len(fluxes) - 1

    # Fit tentative

    x1=down
    x2=up
    a1=0.1
    a2=0.1
    p0 = [A0,B0,x1,x2,a1,a2]

    # flux = np.loadtxt("shutter-clap-laser-0001-first-pulse.data")
    times = np.arange(len(fluxes))
    popt, pcov = curve_fit(model, times, fluxes, p0=p0)
    print popt

    A,B,x1,x2,a1,a2 = popt

    residuals = fluxes - model(times,A,B,x1,x2,a1,a2)

    # error ??
    chi2 = (residuals**2).sum()
    dof = len(fluxes) - 6
    chi2dof = chi2/dof

    print chi2, dof, chi2dof

    pb.figure(1)
    pb.scatter(times, fluxes, marker='+', color='black')
    pb.plot(times, model(times,A,B,x1,x2,a1,a2), color='red')

    pb.figure(2)
    pb.scatter(times, 
               fluxes - model(times,A,B,x1,x2,a1,a2), marker='+', color='black')
    pb.plot(times, np.zeros(shape=(len(times),)), color='red')

    pb.show()
