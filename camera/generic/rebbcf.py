"""
 
 reb_bcf.py -- REB Board Config File: manages a REB from a .bcf file
 
 Author:   J. Kuczewski
 Date:     October 2015
 Version:  0.1
 Location: http://git.kuzew.net/lsst/vst/
    
 Copyright (c) 2015, J. Kuczewski (BNL/LSST)
    
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
    
"""
# Modified by C. Juramy to parse and hold configuration for REB

from ConfigParser import ConfigParser

'''
    Stripe object
    Each stripe has:
        2 ASPICS
        5 DACs
'''
class Stripe(object):

    # equivalence between stripe names and locations
    stripe_map = {'a':0, 'b':1, 'c':2}

    def __init__(self, stripe_addr, stripe_dict):
        self.aspic_dict = stripe_dict['aspic']
        self.bias_dict = stripe_dict['bias']
        self.name = stripe_addr
        self.loc = self.stripe_map[stripe_addr]  # 0,1,2, used to send to FPGA

'''
    REB3 object
    Extends ConfigParser object (maybe a bad idea?)
    Needs bcf_name.
'''
class REBconfig(ConfigParser):
    def __init__(self, bcf_fname, 
                 seq_fname=None,
                 size=None,
                 reb_id=None,
                 ssf=None,
                 ipaddr="tcp://localhost", 
                 img=False):
        ConfigParser.__init__(self)
        self.read(bcf_fname)

        # can override config file with keywords
        # REB ID
        if reb_id is None:
            self.reb_id = self.getint('board', 'id')
        else:
            self.reb_id = reb_id
        
        # SSF File Path
        if ssf is None:
            self.xmlfile = self.get('board', 'ssf')
        else:
            self.xmlfile = ssf

        self.hardware = self.get('board', 'hardware')

        # 2D ADC data: CCD Segment/ADC Channel row/col
        if size is None:
            self.row    = self.getint('board', 'row')
            self.col    = self.getint('board', 'col')
        else:
            self.row = size[0]
            self.col = size[1]
            
        # Used for muilt REB/NIC on same machine
        self.iface  = self.get('board', 'iface')
        self.ipaddress = ipaddr
        #if not img:
            #self.reg_backend = gige.gige(self.reb_id, ipaddr, iface=self.iface)
        #else:
            #self.reg_backend = gige.gige(self.reb_id, ipaddr, iface=self.iface, image=True)
        
        # Process from config file
        self.clock_rails = {}
        for key, val in self.items("global"):
            key = key.split("/")
            if (key[0] == "clock_rails"):
                self.clock_rails[key[1]] = float(val)
                
        # 1 REB has THREE (3) stripes, A => Left, B => Middle, C=> Right
        self.stripes = {}

        self.stripes_enabled = []
        # Process enabled list from config file
        for s in self.get('board', 'stripes_enabled').split(','):
            s = s.strip()
            self.stripes_enabled.append(Stripe.stripe_map[s])  # use location number
            
        # Parse configuration for all stripes
        for s in ['a', 'b', 'c']:
            s = s.strip()
            # Gets passed to stripe object
            stripe_dict = {'aspic' : {}, 'bias'  : {} }

            for key, value in self.items("stripe_%s" % (s)):
                keys = key.split("/")
                # converts to numerical value here
                if keys[0] == 'aspic':
                    stripe_dict['aspic'][keys[1]] = int(value, 16)
                elif keys[0] == 'bias':
                    if keys[1] == 'csgate':
                        stripe_dict['bias'][keys[1]] = int(value, 16)
                    else:
                        stripe_dict['bias'][keys[1]] = float(value)

            sobj = Stripe(s, stripe_dict)
            self.stripes[sobj.loc] = sobj  # save them by location number for compatibility
            

