#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
# XML IO
#

from lxml import etree

from fpga import *

def validate(f):
    """
    To implement. DTD/schema available???
    """
    return True


def process_number(s):
    ss = s.strip()
    try:
        value = int(ss)
    except ValueError:
        value = float(ss)
    return value
    

def process_value(s, params):
    if not(isinstance(s, str)):
        return s, None

    ss = s.strip()

    # replace by the parameter
    print ss
    if params.has_key(ss):
        lvalue = params[ss]
        print "K lvalue = ", lvalue
    else:
        lvalue = ss
        print "NK lvalue = ", lvalue

    # process the unit
    unit = None
    if lvalue[-2:] == 'ns':
        unit = 'ns'
        lvaluenum = lvalue[:-2].strip()
    elif lvalue[-2:] == 'us':
        unit = 'us'
        lvaluenum = lvalue[:-2].strip()
    # elif lvalue[-1:] == 's':
    #     unit = 's'
    #     lvaluenum = lvalue[:-1].strip()
    else:
        lvaluenum = lvalue

    # convert the numeral part
        
    value = process_number(lvaluenum)

    return value, unit



def parse_parameters(tree_node):

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

    parameter_values = \
        dict([(k,parameters[k]['value']) for k in parameters.keys()])

    return parameters, parameter_values

    
def parse_channels(tree):
    channels_desc = {}

    channels_tree = tree.xpath('/sequencer/sequencer-config/channels')
    # print channels_tree

    channels_tree = channels_tree[0]

    cs = channels_tree.xpath('channel')
    # print cs

    for c in cs:
        fullname = c.xpath('fullname/text()')
        name = c.get('id')
        value = c.xpath('value/text()')[0]

        c_dict = { 'channel' : int(value),
                   'name': str(name) }
        
        if fullname != None:
            c_dict['fullname'] = fullname[0]

        channels_desc[name] = dict(c_dict)

    channels = ChannelMap( [v['channel'] for v in channels_desc.values()],
                           [v['name']    for v in channels_desc.values()] )


    return channels_desc, channels
    

def parse_functions(tree, channels_desc, channels, parameters):
    functions = {}

    functions_tree = tree.xpath('/sequencer/sequencer-config/functions')
    # print functions_tree

    functions_tree = functions_tree[0]

    funcs = functions_tree.xpath('function')
    # print funcs

    idfunc = 0
    for func in funcs:
        fullname =  func.xpath('fullname/text()')[0]
        name =  func.get('id')
        
        func_dict = { }

        func_dict['idfunc'] = idfunc
        if fullname != None:
             func_dict['fullname'] = fullname[0]

        functions[name] = dict(func_dict)

        print name, fullname

        function = Function(name = name, 
                            fullname = fullname, 
                            channels = channels)

        # analyzing constants

        constants = {}
        for const in func.xpath('constants/constant'):
            print const
            channel = const.get('ref')
            print channel
            # print const.xpath('text()')
            value = int(const.xpath('text()')[0])
            print value
            constants[channel] = value
        
        print constants

        # analyzing slices

        channel_position = {}
        cpos = 0
        for clock in func.xpath('clocklist/clock'):
            print clock
            cname = clock.get('ref')
            channel_position[cname] = cpos
            cpos += 1

        print channel_position

        # self.timelengths = {0: 12, 1: 14}
        # self.outputs = {0: '0b01001101...', 1: '0b1111000...', ... }
        timelengths = {}
        outputs = {}

        islice = 0
        for timeslice in func.xpath('slicelist/timeslice'):
            slice_id = timeslice.get('id')

            lduration = timeslice.xpath('duration/text()')[0]
            duration, unit = process_value(lduration, parameters)
            if unit == 'ns':
                duration /= 10.0  # TODO: improve this

            timelengths[islice] = int(duration)

            output = 0x0000000000000000

            svalue = timeslice.xpath('value/text()')[0].strip()

            for ck, cdesc in channels_desc.iteritems():
                cname = cdesc['name']
                crank = cdesc['channel']

                if constants.has_key(cname):
                    # that's a constant one
                    output |= (constants[cname]<<crank)
                elif channel_position.has_key(cname):
                    cpos = channel_position[cname]
                    cval = int(svalue[cpos])
                    output |= (cval<<crank)

            print bin(output)

            outputs[islice] = output
                    
            islice += 1

        function.timelengths = dict(timelengths)
        function.outputs = dict(outputs)
        
        functions[idfunc] = function
        idfunc += 1

    return functions





def parse_call(call_node, prg, params):
    """
    Parse a simple <call> node. Return either an unnamed subroutine or an instruction.
    """
    
    print "        call"

    repeats = call.xpath('repeat/text()')
    if repeats == None:
        repeat = 1
    elif len(repeats) < 1:
        repeat = 1
    else:
        repeat = repeats[0]

        rep = process_arg(repeat, parameter_values)

            # print "            repeat = ", repeat, rep


            # if call.get('ref') == None:
            #     print "            unnamed subroutine"
            #     unnamed_subroutine_name = "unnamed%04d" % unnamed_num
            #     unnamed_num += 1
            #     prg.subroutines[unnamed_subroutine_name] = Subroutine()
                
            # else:
            #     print "            calling", call.get('ref')
            #     called = str(call.get('ref')).strip()
                
            #     # is it a 'function' call?
            #     if called in functions.keys():
            #         instr = Instruction(opcode = Instruction.OP_CallFunction,
            #                             function_id = functions[called]['idfunc'],
            #                             infinite_loop = False,
            #                             repeat = rep)
                    
            #         print instr
            #     else:
            #         instr = Instruction(opcode = Instruction.OP_JumpToSubroutine,
            #                             subroutine = called,
            #                             infinite_loop = False,
            #                             repeat = rep)
            #         print instr
                
            #     prg.subroutines[subroutine_name].instructions.append(instr)





def xmlparse(f):
    tree = etree.parse(f)
    
    # validation phase???
    # DTD ???




    return 0



    # Looking for all subroutines

    prg = Program_UnAssembled()

    subroutines_tree = tree.xpath('/sequencer/sequencer-routines')
    print subroutines_tree
    if len(subroutines_tree) != 1:
        raise IOError('Invalid XML file')
    subroutines_tree = subroutines_tree[0]

    subs = subroutines_tree.xpath(
        'subroutines/subroutine')
    print subs

    mains = subroutines_tree.xpath(
        'mains/main')
    print mains

    allsubs = subs + mains

    unnamed_num = 0

    for sub in allsubs:
        print "subroutine"
        print "   name = ", sub.get('id')
        print "   fullname = ", sub.xpath('fullname/text()')


        subroutine_name = str(sub.get('id'))
        prg.subroutines[subroutine_name] = Subroutine()

        calls = sub.xpath('call')
        # for call in calls:





        


    # return parameters, parameter_values, channels, functions, prg



# ps = xmlparse('sequencer-transcript.xml')
# ps = xmlparse('sequencer-soi.xml')





tree = etree.parse('sequencer-soi.xml')

pdesc, params = parse_parameters(tree)
cdesc, channels = parse_channels(tree)

functions = parse_functions(tree, cdesc, channels, params)
