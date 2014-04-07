#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
# XML IO
#

# En cours...

from lxml import etree

from fpga import *

def validate(f):
    pass

def xmlparse(f):
    tree = etree.parse(f)
    
    # validation phase???
    # DTD ???

    # Looking for all subroutines

    subroutines_tree = tree.xpath('/sequencer/sequencer-routines')
    print subroutines_tree
    if len(subroutines_tree) != 1:
        raise IOError('Invalid XML file')
    subroutines_tree = subroutines_tree[0]

    subs = subroutines_tree.xpath(
        'subroutines/subroutine')
    print subs
    for sub in subs:
        print "subroutine"
        print "   name = ", sub.get('id')
        print "   fullname = ", sub.xpath('fullname/text()')

        calls = sub.xpath('call')
        for call in calls:
            print "        call"
            if call.get('ref') == None:
                print "            unnamed subroutine"
                
            else:
                print "            calling", call.get('ref')

            repeats = call.xpath('repeat/text()')
            if repeats == None:
                repeat = 1
            elif len(repeats) < 1:
                repeat = 1
            else:
                repeat = repeats[0]

            print "            repeat = ", repeat


    parameters = {}

    parameters_tree = tree.xpath('/sequencer/sequencer-config/parameters')
    print parameters_tree
    # if len(parameters) >= 1:
    parameters_tree = parameters_tree[0]

    params = parameters_tree.xpath('parameter')
    print params

    for param in params:
        fullname = param.xpath('fullname/text()')[0]
        name = param.get('id')
        value = param.xpath('value/text()')[0]

        param_dict = { 'value' : value }
        
        if fullname != None:
            param_dict['fullname'] = fullname

        parameters[name] = dict(param_dict)


    channels = {}

    channels_tree = tree.xpath('/sequencer/sequencer-config/channels')
    print channels_tree
    # if len(channels) >= 1:
    channels_tree = channels_tree[0]

    cs = channels_tree.xpath('channel')
    print cs

    for c in cs:
        fullname = c.xpath('fullname/text()')
        name = c.get('id')
        value = c.xpath('value/text()')[0]

        c_dict = { 'value' : value }
        
        if fullname != None:
            c_dict['fullname'] = fullname[0]

        channels[name] = dict(c_dict)


    functions = {}

    functions_tree = tree.xpath('/sequencer/sequencer-config/functions')
    print functions_tree
    # if len(functions) >= 1:
    functions_tree = functions_tree[0]

    funcs = functions_tree.xpath('function')
    print funcs

    for func in funcs:
        fullname =  func.xpath('fullname/text()')
        name =  func.get('id')
        value =  func.xpath('value/text()')[0]

        clocks    = func.xpath('clocklist')
        slices    = func.xpath('slicelist')
        constants = func.xpath('constants')

        func_dict = { 'value' : value }
        
        if fullname != None:
             func_dict['fullname'] = fullname[0]

        functions[name] = dict(func_dict)


    return parameters, channels, functions



ps = xmlparse('sequencer-transcript.xml')


