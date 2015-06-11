
import numpy as np
from scipy.optimize import curve_fit


flux = np.loadtxt("shutter-clap-laser-0001-first-pulse.data")
time = np.arange(len(flux))

def func(x, A,B,x1,x2,a1,a2):
    return A*.25*(1+np.tanh(a1*(x-x1)))*(1-np.tanh(a2*(x-x2))) + B

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
