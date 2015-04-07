#! /usr/bin/env python
#
# LSST
# Python minimal interface for the REB FPGA
# XML IO
#

from lxml import etree

from fpga import *

class XMLParser(object):

    def __init__(self):

        self.channels_desc = {}
        self.channels = {}
        self.parameters_desc = {}
        self.parameters = {}
        self.functions = {}
        self.functions_desc = {}
        self.subroutines = {}
        self.subroutines_names = []
        self.mains = {}
        self.mains_names = []
        self.unnamed_subroutine_num = 0


    def process_number(self, s):
        ss = s.strip()
        try:
            value = int(ss)
        except ValueError:
            value = float(ss)

        return value

    def process_value(self, s):
        if not(isinstance(s, str)):
            return s, None

        ss = s.strip()

        # replace by the parameter
        # print ss
        if self.parameters.has_key(ss):
            lvalue = self.parameters[ss]
            # print "K lvalue = ", lvalue
        else:
            lvalue = ss
            # print "NK lvalue = ", lvalue

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
        value = self.process_number(lvaluenum)

        return value, unit

    
    def parse_parameters(self, parameters_node):

        params = parameters_node.xpath('parameter')
        # print params

        for param in params:
            fullname = param.xpath('fullname/text()')[0]
            name = param.get('id')
            value = param.xpath('value/text()')[0]
            
            param_dict = { 'value' : value }
        
            if fullname != None:
                param_dict['fullname'] = fullname

            self.parameters_desc[name] = dict(param_dict)

        self.parameters = \
            dict([(k, self.parameters_desc[k]['value']) 
                  for k in self.parameters_desc.keys()])


    def parse_channels(self, channels_node):

        cs = channels_node.xpath('channel')
        # print cs

        for c in cs:
            fullname = c.xpath('fullname/text()')
            name = c.get('id')
            value = c.xpath('value/text()')[0]

            c_dict = { 'channel' : int(value),
                       'name': str(name) }
        
            if fullname != None:
                c_dict['fullname'] = fullname[0]

            self.channels_desc[name] = dict(c_dict)

        self.channels = bidi.BidiMap( [v['channel'] 
                                       for v in self.channels_desc.values()],
                                      [v['name']    
                                       for v in self.channels_desc.values()] )
    

    def parse_functions(self, functions_node):

        funcs = functions_node.xpath('function')
        # print funcs

        idfunc = 0
        for func in funcs:
            fullname =  func.xpath('fullname/text()')[0]
            name =  func.get('id')
        
            func_dict = { }

            func_dict['idfunc'] = idfunc
            if fullname != None:
                func_dict['fullname'] = fullname

            self.functions_desc[name] = dict(func_dict)

            print name, fullname

            function = Function(name = name, 
                                fullname = fullname, 
                                channels = self.channels)

            # analyzing constants

            constants = {}
            for const in func.xpath('constants/constant'):
                # print const
                channel = const.get('ref')
                # print channel
                # print const.xpath('text()')
                value = int(const.xpath('text()')[0])
                # print value
                constants[channel] = value
        
            # print constants

            # analyzing slices

            channel_position = {}
            cpos = 0
            for clock in func.xpath('clocklist/clock'):
                # print clock
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
                duration, unit = self.process_value(lduration)
                if unit == 'ns':
                    duration /= 10.0  # TODO: improve this

                if islice == 0:
                    timelengths[islice] = int(duration)-1  # FPGA adds one to duration of first slice
                elif islice == len(func.xpath('slicelist/timeslice'))-1:
                    timelengths[islice] = int(duration)-2  # FPGA adds 2 to duration of last slice
                else:
                    timelengths[islice] = int(duration)

                output = 0x0000000000000000

                svalue = timeslice.xpath('value/text()')[0].strip()

                for ck, cdesc in self.channels_desc.iteritems():
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
        
            self.functions_desc[name]['function'] = function
            self.functions[name] = function
            idfunc += 1


    def parse_call(self, call_node):
        """
        Parse (recursively) a simple <call> node. 
        Return an instruction; update the dictionary of subroutines
        """

        print "        call"

        repeat = 1
        repeats = call_node.xpath('repeat/text()')
        if (repeats != None) and (len(repeats) >= 1):
            srepeat = repeats[0]
            lvalue, lunit = self.process_value(srepeat)
            repeat = lvalue

        print "            repeat = ", repeat

        if call_node.get('ref') != None:
            print "            calling", call_node.get('ref')
            called = str(call_node.get('ref')).strip()

            # is it a 'function' call?
            if self.functions_desc.has_key(called):
                instr = Instruction(opcode = Instruction.OP_CallFunction,
                                    function_id = self.functions_desc[called]['idfunc'],
                                    infinite_loop = False,
                                    repeat = repeat)
                print instr
                return instr

            # else, is it a 'subroutine' call (jump)?
            # do we check that the subroutine exists? even if defined later?
            # elif subs.has_key(called):
            else:
                instr = Instruction(opcode = Instruction.OP_JumpToSubroutine,
                                    subroutine = called,
                                    infinite_loop = False,
                                    repeat = repeat)
                print instr
                return instr

            # else:
            #     # undefined call...
            #     raise ValueError("Call to undefined object '%s'" % called)

        else: # unnamed subroutine

            subcalls = call_node.xpath("call")

            unnamed = Subroutine()
            unnamed.name = "unnamed%04d" % self.unnamed_subroutine_num
            self.unnamed_subroutine_num += 1

            print "unnamed subroutine", unnamed.name

            for subcall in subcalls:
                subinstr = self.parse_call(subcall)
                unnamed.instructions.append(subinstr)

            # Add the final RTS
            unnamed.instructions.append(
                Instruction(opcode = Instruction.OP_ReturnFromSubroutine))

            instr = Instruction(opcode = Instruction.OP_JumpToSubroutine,
                                subroutine = unnamed.name,
                                infinite_loop = False,
                                repeat = repeat)

            self.subroutines[unnamed.name] = unnamed
            self.subroutines_names.append(unnamed.name)

            return instr

    def parse_subroutine(self, sub_node):
        # print "subroutine"
        subname =  sub_node.get('id')
        fullname =  sub_node.xpath('fullname/text()')[0]
        print "   name = ", subname
        # print "   fullname = ", fullname
        
        sub = Subroutine()
        sub.name = subname
        sub.fullname = fullname

        calls = sub_node.xpath('call')
        for call_node in calls:
            c_instr = self.parse_call(call_node)
            sub.instructions.append(c_instr)

        # Add the file RTS opcode at the end
        sub.instructions.append(
            Instruction(opcode = Instruction.OP_ReturnFromSubroutine))

        return sub

    def parse_subroutines(self, subroutines_node):

        subs_nodes = subroutines_node.xpath('subroutine')

        for sub_node in subs_nodes:
            sub = self.parse_subroutine(sub_node)
            self.subroutines[sub.name] = sub
            self.subroutines_names.append(sub.name)


    def parse_mains(self, mains_node):

        mains_nodes = mains_node.xpath('main')

        for main_node in mains_nodes:
            main = self.parse_subroutine(main_node)
            self.mains[main.name] = main
            self.mains_names.append(main.name)


    def parse_tree(self, tree_node):

        self.unnamed_subroutine_num = 0

        # Get the parameters
        parameters_node = tree_node.xpath(
            '/sequencer/sequencer-config/parameters')
        # print parameters_node
        parameters_node = parameters_node[0]
        self.parse_parameters(parameters_node)

        # parse the channel descriptions
        channels_node = tree_node.xpath('/sequencer/sequencer-config/channels')
        channels_node = channels_node[0]
        self.parse_channels(channels_node)

        # parse the sequencer functions
        functions_node = tree_node.xpath(
            '/sequencer/sequencer-config/functions')
        functions_node = functions_node[0]
        self.parse_functions(functions_node)

        # Parse all subroutines 
        subroutines_node = tree_node.xpath(
            '/sequencer/sequencer-routines/subroutines')
        subroutines_node = subroutines_node[0]
        self.parse_subroutines(subroutines_node)
        print "SUBS", self.subroutines_names

        # Parse all 'mains' 
        mains_node = tree_node.xpath('/sequencer/sequencer-routines/mains')
        mains_node = mains_node[0]
        self.parse_mains(mains_node)
        print "MAINS", self.mains_names

        # TODO: Modify for new sequencer: mains should now be written in memory as mains with END at the end,
        # we will use 0x340000 to point to the right one.
        allsubs = dict(self.mains)
        allsubs.update(self.subroutines)
        allsubsnames = self.mains_names + self.subroutines_names

        # Produce a minimal main (a jump (JSR) and end-of-program (END))
        # It points to the first 'main'.

        supermain = [ Instruction(opcode = Instruction.OP_JumpToSubroutine,
                                  subroutine = self.mains_names[0]),
                      Instruction(opcode = Instruction.OP_EndOfProgram) ]

        # Create the unassembled program

        self.prg = Program_UnAssembled()
        
        self.prg.subroutines = allsubs # key = name, value = subroutine object
        self.prg.subroutines_names = allsubsnames # to keep the order
        self.prg.instructions = supermain # main program instruction list

        return ( self.prg, 
                 self.functions_desc, 
                 self.parameters_desc, 
                 self.channels_desc )


    def parse_file(self, xmlfile):
        tree = etree.parse(xmlfile)
        return self. parse_tree(tree)

    def validate_file(self, xmlfile):
        """
        To implement. DTD/schema available???
        """
        return True



# @classmethod
# def fromxmlfile(cls, xmlfile):
def fromxmlfile(xmlfile):
    """
    Create and return a Sequencer instance from a XML file.
    Raise an exception if the syntax is wrong.
    """


    channels = {}
    channels_desc = {}
    functions = {}
    functions_desc = {}
    
    parser = XMLParser()
    ( prg, 
      functions_desc, 
      parameters_desc, 
      channels_desc ) = parser.parse_file(xmlfile)
    
    program = prg.compile()
    
    channels = bidi.BidiMap( [v['channel'] 
                              for v in channels_desc.values()],
                             [v['name']    
                              for v in channels_desc.values()] )
    
    for k,v in functions_desc.iteritems():
        functions[v['idfunc']] = v['function']
        
        
    seq = Sequencer(channels = channels, 
                    channels_desc = channels_desc, 
                    functions = functions, 
                    functions_desc = functions_desc, 
                    program = program)

    return seq


Sequencer.fromxmlfile = staticmethod(fromxmlfile)


# tree = etree.parse('sequencer-soi.xml')


# P = XMLParser()
# pr,fu = P.parse_file('sequencer-soi.xml')


