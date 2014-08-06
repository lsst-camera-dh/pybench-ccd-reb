
import numpy as np

class Grid(object):
    """
    Grid iterator. Useful to optimize the path on the grid.
    Order may be 'normal' or 'faster'.

    Examples:

    g = Grid(xmin =  0, xmax = 10, dx = 1, 
             ymin = -3, ymax =  3, dy = 1)

    g = Grid(xmin =  0, xmax = 10, dx = 1, 
             ymin = -3, ymax =  3, dy = 1, 
             reference = {'x':10,'y':-34, 'period':20})

    g = Grid(xmin =  0, xmax = 10, dx = 1, 
             ymin = -3, ymax =  3, dy = 1, 
             reference = {'x':10,'y':-34, 'period':20},
             spread = {'n': 50, 'period':50})
    """

    def __init__(self, 
                 xmin, xmax, dx, ymin, ymax, dy, order="faster",
                 reference = None):
        self.xrange = list(np.arange(xmin, xmax, dx))
        self.yrange = list(np.arange(ymin, ymax, dy))

        self.nx = len(self.xrange)
        self.ny = len(self.yrange)
        self.ix = 0
        self.iy = 0

        if order not in ['normal', 'faster']:
            raise ValueError("invalid order: " +
                             "only 'normal' and 'faster' are available.")
            
        self.order = order

        if reference != None:
            if ( not(reference.has_key('x')) or
                 not(reference.has_key('y')) or
                 not(reference.has_key('period')) ):
                raise ValueError(
                    "invalid format for reference parameter." +
                    " Should be a dictionary with keys 'x', 'y' and 'period'")

            if reference['period'] < 2:
                raise ValueError(
                    "'period' should be >= 2 otherwise it will loop forever.")

        self.reference = reference # dict with keys : x, y, period
        self.refi = 0


    def __iter__(self):
        return self

    def next(self):

        if ( (self.reference != None) and 
             ((self.refi % self.reference['period']) == 0) ):
            # it is time to go back to the reference point
            self.refi += 1
            nextpos = (self.reference['x'], self.reference['y'])
            return nextpos

        if (self.ix > self.nx - 1):
            raise StopIteration("End of Loop")

        if (self.iy > self.ny - 1):
            self.iy = 0
            self.ix += 1
            if self.order == 'faster':
                self.yrange.reverse()

        if (self.ix > self.nx - 1):
            raise StopIteration("End of Loop")

        self.refi += 1
        nextpos = self.xrange[self.ix], self.yrange[self.iy]
        self.iy += 1
        
        return nextpos
        
            
