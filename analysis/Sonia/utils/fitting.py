'''
Created on Aug 20, 2014

@author: karkar
'''

from scipy import optimize
from numpy import *

class Parameter:
    def __init__(self, value):
            self.value = value

    def set(self, value):
            self.value = value

    def __call__(self):
            return self.value

def fit(function, parameters, y, x = None):
    def f(params):
        i = 0
        for p in parameters:
            p.set(params[i])
            i += 1
        return y - function(x)

    if x is None: x = arange(y.shape[0])
    p = [param() for param in parameters]
    optimize.leastsq(f, p)

# optimize.curve_fit(f, xdata, ydata)
    
def GetBestRange(function,nparam, y, MinPoints):
    #function is the function to be fitted on the data
    #nparam is the number of parameters , y, MinPoints
    x = arange(y.shape[0])
#     print x, x.shape[0]
#     print y, y.shape[0]
    paramlist = []
#     covariancelist= []
    perrlist = []
    xcut = []
    for n in range (MinPoints, len(x)+1): 
        for i in range(0,len(x)-n+1):
            cut = x[i:i+n]
#             print cut
#             if x[cut].shape[0] < 3: continue
#             print "xaxis = ", x[cut]
#             print "data :", y[cut]
            xcut.append(x[cut])
            popt, pcov = optimize.curve_fit(function, x[cut], y[cut])
#             print  popt, pcov 
            paramlist.append(popt)
#             covariancelist.append(pcov)
            perrlist.append(sqrt(diag(pcov)))
            del cut
#     paramarray = array(paramlist)    
#     print "all parameters :" , paramarray
#     print " all cov matrix :" , covariancelist
    perrarray = array(perrlist)
#     print "all perr:", perrarray    
#     print min(perrarray)
    minindex = argmin(perrarray)
    xopt = xcut[minindex]
    yopt = y[xopt]
    popt = paramlist[minindex]
    return minindex, xopt, yopt, popt
    
        
    