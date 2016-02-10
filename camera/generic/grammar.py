#
# Grammar for the REB3 sequencer language
# (sequencer with variables)
#
# Author: Laurent Le Guillou

import re

class SeqParser(object):

    #-----------------------------------------------------------------------

    # ZMSP ::= [ \t]* # zero or more spaces
    _p_zmsp = "([ \t]*)"

    # OMSP ::= [ \t]+ # one or more spaces
    _p_omsp = "([ \t]+)"

    # NEWLINE ::= (\n | \r\n | \r) # newline
    _p_newline = "(\n|\r\n|\r)"

    # COMMENT ::= '#' .*  [until NEWLINE]
    # _p_comment = "\#(\.*)$"
    _p_comment = "#(.*)"
    
    # INTEGER ::= [0-9]+
    _p_integer = "(\d+)"

    # NAME ::= [A-Za-z][0-9A-Za-z\_]*
    _p_name = "([A-Za-z][\dA-Za-z\_]*)"

    # DURATION_UNIT ::= ( 'ns' | 'us' | 'ms' | 's' )
    _p_duration_unit = "(ns|us|ms|s)"
    
    #-----------------------------------------------------------------------

    def __init__(self, s):
        self.s = s
        self.length = len(self.s)
        
        # compiling patterns
        self.p_zmsp =    re.compile("^" + self._p_zmsp)
        self.p_omsp =    re.compile("^" + self._p_omsp)
        self.p_newline = re.compile("^" + self._p_newline)
        self.p_comment = re.compile("^" + self._p_comment)
        self.p_integer = re.compile("^" + self._p_integer)
        self.p_name =    re.compile("^" + self._p_name)
        self.p_duration_unit = re.compile("^" + self._p_duration_unit)

    #=======================================================================

    #-----------------------------------------------------------------------
    # ZMSP ::= [ \t]* # zero or more spaces
    # OMSP ::= [ \t]+ # one or more spaces

    def m_zmsp(self, pos):
        if pos >= self.length:
            return pos

        # Always match, eat spaces
        matches = self.p_zmsp.search(self.s[pos:])
        if matches == None:
            return pos

        l = matches.end()
        pnext = pos + l
        return pnext


    def m_omsp(self, pos):
        # At least on space
        if pos >= self.length:
            return None
        
        matches = self.p_omsp.search(self.s[pos:])
        if matches == None:
            return None

        l = matches.end()
        pnext = pos + l
        return pnext
    
    #-----------------------------------------------------------------------
    # NEWLINE ::= (\n | \r\n | \r)

    def m_newline(self, pos):
        if pos >= self.length:
            return None

        matches = self.p_newline.search(self.s[pos:])
        if matches == None:
            return None

        # start = matches.start()
        l = matches.end()
        pnext = pos + l

        return pnext

    #-----------------------------------------------------------------------
    # COMMENT ::= \#(.*) [NEWLINE]

    def m_comment(self, pos):
        if pos >= self.length:
            return None

        matches = self.p_comment.search(self.s[pos:])
        if matches == None:
            return None

        # start = matches.start()
        l = matches.end()
        comment = matches.group(1)
        pnext = pos + l

        return pnext, comment

    #-----------------------------------------------------------------------
    # EMPTY_LINE ::= SPACE* COMMENT? NEWLINE

    def m_empty_line(self, pos):
        if pos >= self.length:
            return None

        pnext = self.m_zmsp(pos)

        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext

        return pnext
    
    #-----------------------------------------------------------------------
    # INTEGER ::= [0-9]+

    def m_integer(self, pos):
        if pos >= self.length:
            return None

        matches = self.p_integer.search(self.s[pos:])
        if matches == None:
            return None

        # start = matches.start()
        l = matches.end()
        integer = int(matches.group(1))
        pnext = pos + l

        return (pnext, integer)

    #-----------------------------------------------------------------------
    # NAME ::= [A-Za-z][0-9A-Za-z\_]*

    def m_name(self, pos):
        if pos >= self.length:
            return None

        matches = self.p_name.search(self.s[pos:])
        if matches == None:
            return None

        # start = matches.start()
        l = matches.end()
        name = matches.group(1)
        pnext = pos + l

        return (pnext, name)

    #-----------------------------------------------------------------------
    # XXX_SECTION_MARKER = "[XXX]" SPACE* COMMENT? NEWLINE

    _p_section_marker = "[%s]"
    
    def m_section_marker(self, pos, section_name):
        if pos >= self.length:
            return None

        s_section_marker = self._p_section_marker % section_name
        l = len(s_section_marker)
        
        if ( self.s[pos:pos+l] != s_section_marker ):
            return None

        pnext = pos + l

        pnext = self.m_zmsp(pnext)
        
        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        # if r != None:
        #     pnext = r[0]
        #     print pnext
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext
        
        return pnext, section_name

    #=======================================================================

    #-----------------------------------------------------------------------
    # DURATION_UNIT ::= ( 'ns' | 'us' | 'ms' | 's' )
    # DURATION_VALUE ::= INTEGER SPACE* DURATION_UNIT

    def m_duration_unit(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        print pnext

        matches = self.p_name.search(self.s[pos:])
        if matches == None:
            return None

        # start = matches.start()
        l = matches.end()
        unit = matches.group(1)
        pnext = pos + l

        return (pnext, unit)


    def m_duration_value(self, pos):
        if pos >= self.length:
            return None

        pnext = pos

        r = self.m_integer(pnext)
        if r == None:
            return None
        pnext, integer = r
        print "INTEGER =", integer
        print pnext

        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_duration_unit(pnext)
        if r == None:
            return None
        pnext, unit = r
        print "INTEGER =", unit
        print pnext

        return pnext, (integer, unit)

    #=======================================================================

    #-----------------------------------------------------------------------
    # CONSTANT_NAME ::= NAME
    # CONSTANT_VALUE ::= DURATION_VALUE | INTEGER
    # CONSTANT_DEF_LINE ::=
    #   SPACE* CONSTANT_NAME SPACE* ':' CONSTANT_VALUE SPACE* COMMENT? NEWLINE
    # 
    # CONSTANT_SECTION_MARKER ::= '[constants]' SPACE* COMMENT? NEWLINE
    #
    # CONSTANT_SECTION ::=
    #   CONSTANT_SECTION_MARKER ( EMPTY_LINE | CONSTANT_DEF_LINE )*

    def m_constant_name(self, pos):
        return self.m_name(pos)

    def m_constant_value(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        r = self.m_duration_value(pnext)
        if r != None:
            pnext, constant_value = r
            return pnext, constant_value

        r = self.m_integer(pnext)
        if r != None:
            pnext, integer = r
            return pnext, integer

        return None

    def m_constant_def_line(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        print pnext
        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_constant_name(pnext)
        if r == None:
            return None
        pnext, constant_name = r
        print "CONSTANT_NAME =", constant_name
        print pnext

        pnext = self.m_zmsp(pnext)

        if self.s[pnext] != ':':
            return None
        pnext += 1
        print ":"
        print pnext

        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_constant_value(pnext)
        if r == None:
            return None
        pnext, constant_value = r
        print pnext, constant_value

        pnext = self.m_zmsp(pnext)
        print pnext

        comment = ''
        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        # if r != None:
        #     pnext = r[0]
        #     print pnext
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext
        
        return pnext, (constant_name, constant_value, comment)

    #-----------------------------------------------------------------------
    # CONSTANT_SECTION ::=
    #   CONSTANT_SECTION_MARKER ( EMPTY_LINE | CONSTANT_DEF_LINE )*

    def m_constant_section(self, pos):
    
        if pos >= self.length:
            return None

        constant_defs = []
        
        pnext = pos

        print pnext
        r = self.m_section_marker(pnext, "constants")
        if r == None:
            return None
        pnext, section_name = r
        
        while True:
            r = self.m_empty_line(pnext)
            print "[A]", pnext, r
            if r != None:
                pnext = r
                continue

            r = self.m_constant_def_line(pnext)
            print "[B]", pnext, r
            if r != None:
                pnext, constant_def = r
                constant_defs.append(constant_def)
                continue

            break

        return pnext, constant_defs
                
    #=======================================================================

    #-----------------------------------------------------------------------
    # CLOCK_NAME ::= NAME
    # CLOCK_ID   ::= INTEGER
    # CLOCK_DEF_LINE  ::=
    #   SPACE* CLOCK_NAME SPACE* ':' CLOCK_ID SPACE* COMMENT? NEWLINE
    #
    # CLOCK_SECTION_MARKER ::= '[clocks]' SPACE* COMMENT? NEWLINE
    #
    # CLOCK_SECTION ::= CLOCK_SECTION_MARKER ( EMPTY_LINE | CLOCK_DEF_LINE )*
    #
    
    def m_clock_name(self, pos):
        return self.m_name(pos)

    def m_clock_id(self, pos):
        return self.m_integer(pos)

    def m_clock_def_line(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        print pnext
        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_clock_name(pnext)
        if r == None:
            return None
        pnext, clock_name = r
        print "CLOCK_NAME =", clock_name
        print pnext

        pnext = self.m_zmsp(pnext)

        if self.s[pnext] != ':':
            return None
        pnext += 1
        print ":"
        print pnext

        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_clock_id(pnext)
        if r == None:
            return None
        pnext, clock_id_s = r
        clock_id = int(clock_id_s)
        print "CLOCK_ID =", clock_id
        print pnext

        pnext = self.m_zmsp(pnext)
        print pnext

        comment = ''
        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        # if r != None:
        #     pnext = r[0]
        #     print pnext
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext
        
        return pnext, (clock_name, clock_id, comment)
    
    #-----------------------------------------------------------------------
    # CLOCK_SECTION ::= CLOCK_SECTION_MARKER ( EMPTY_LINE | CLOCK_DEF_LINE )*

    def m_clock_section(self, pos):
    
        if pos >= self.length:
            return None

        clock_defs = []
        
        pnext = pos

        print pnext
        r = self.m_section_marker(pnext, "clocks")
        if r == None:
            return None
        pnext, section_name = r
        
        while True:
            r = self.m_empty_line(pnext)
            print "[A]", pnext, r
            if r != None:
                pnext = r
                continue

            r = self.m_clock_def_line(pnext)
            print "[B]", pnext, r
            if r != None:
                pnext, clock_def = r
                clock_defs.append(clock_def)
                continue

            break

        return pnext, clock_defs
                
    #=======================================================================
    #
    # PTR_NAME ::= NAME
    #
    # REP_FUNC_DEF_LINE ::=
    # SPACE* 'REP_FUNC' SPACE+ PTR_NAME SPACE+ INTEGER SPACE* COMMENT? NEWLINE
    # 
    # REP_SUBR_DEF_LINE ::=
    # SPACE* 'REP_SUBR' SPACE+ PTR_NAME SPACE+ INTEGER SPACE* COMMENT? NEWLINE
    # 
    # PTR_FUNC_DEF_LINE ::=
    # SPACE* 'PTR_FUNC' SPACE+ PTR_NAME SPACE+ (FUNC_NAME | FUNC_ID) SPACE* COMMENT? NEWLINE
    #
    # PTR_SUBR_DEF_LINE ::=
    # SPACE* 'PTR_SUBR' SPACE+ PTR_NAME SPACE+ (SUBR_NAME | ADDRESS) SPACE* COMMENT? NEWLINE
    #
    
    def m_ptr_name(self, pos):
        return self.m_name(pos)

    # ...

    #=======================================================================
    #
    # FUNC_NAME ::= NAME
    #
    # FUNC_NAME_DEF_LINE ::=
    #   SPACE* FUNC_NAME SPACE* ':' SPACE* COMMENT? NEWLINE
    #
    # FUNC_CLOCKS_MARKER ::= 'clocks'
    #
    # FUNC_CLOCKS_NAMES_LINE ::=
    #   SPACE* FUNC_CLOCKS_MARKER SPACE* ':'
    #   SPACE* CLOCK_NAME SPACE* (',' SPACE* CLOCK_NAME SPACE*)*
    #
    # FUNC_SLICES_MARKER ::= 'slices'
    # 
    # FUNC_SLICES_MARKER_LINE ::=
    #   SPACE* FUNC_SLICES_MARKER ':' SPACE* COMMENT? NEWLINE
    #
    # FUNC_SLICE_DEF_LINE ::=
    #   SPACE* ( DURATION_VALUE | CONSTANT_NAME ) SPACE* '='
    #   SPACE* ( '0' | '1' ) SPACE* (',' SPACE* ( '0' | '1' ) SPACE* )*
    #   SPACE* COMMENT? NEWLINE
    # 
    # FUNC_SLICES_DEFS_BLOCK ::=
    #   FUNC_SLICES_MARKER_LINE
    #   EMPTY_LINE*
    #   FUNC_SLICE_DEF_LINE
    #   ( FUNC_SLICE_DEF_LINE | EMPTY_LINE )*
    #
    # FUNC_CONSTANTS_MARKER ::= 'constants'
    #
    # FUNC_CONSTANTS_DEFS_LINE ::=
    #   SPACE* FUNC_CONSTANTS_MARKER SPACE* ':'
    #   SPACE* CLOCK_NAME SPACE* '=' SPACE* ( '0' | '1' )
    #   (',' SPACE* CLOCK_NAME SPACE* '=' SPACE* ( '0' | '1' ) )*
    #   SPACE* COMMENT? NEWLINE
    # 
    # FUNC_DEF_BLOCK ::=
    #   FUNC_NAME_DEF_LINE
    #   EMPTY_LINE*
    #   FUNC_CLOCKS_NAMES_LINE
    #   EMPTY_LINE*
    #   FUNC_SLICES_DEFS_BLOCK
    #   EMPTY_LINE*
    #   FUNC_CONSTANTS_DEFS_LINE
    #   EMPTYLINES
    #

    #-----------------------------------------------------------------------
    # FUNC_NAME ::= NAME

    def m_func_name(self, pos):
        return self.m_name(pos)


    #-----------------------------------------------------------------------
    # FUNC_NAME_DEF_LINE ::=
    #   SPACE* FUNC_NAME SPACE* ':' SPACE* COMMENT? NEWLINE

    def m_func_name_def_line(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        print pnext
        pnext = self.m_zmsp(pnext)
        print pnext

        r = self.m_func_name(pnext)
        if r == None:
            return None
        pnext, func_name = r
        print "FUNC_NAME =", func_name
        print pnext

        pnext = self.m_zmsp(pnext)

        if self.s[pnext] != ':':
            return None
        pnext += 1
        print ":"
        print pnext

        pnext = self.m_zmsp(pnext)
        print pnext

        comment = ''
        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext
        
        return pnext, (func_name, comment)

    #-----------------------------------------------------------------------
    # FUNC_CLOCKS_MARKER ::= 'clocks'
    #
    # FUNC_CLOCKS_NAMES_LINE ::=
    #   SPACE* FUNC_CLOCKS_MARKER SPACE* ':'
    #   SPACE* CLOCK_NAME SPACE* (',' SPACE* CLOCK_NAME SPACE*)*
    #

    _s_func_clocks_marker = "clocks"
    
    def m_func_clocks_names_line(self, pos):
        if pos >= self.length:
            return None

        pnext = pos
        print pnext
        pnext = self.m_zmsp(pnext)
        print pnext

        l = len(self._s_func_clocks_marker)
        if self.s[pnext:pnext+l] != self._s_func_clocks_marker:
            return None
        pnext += l

        pnext = self.m_zmsp(pnext)

        if self.s[pnext] != ':':
            return None
        pnext += 1
        
        pnext = self.m_zmsp(pnext)

        clock_names = []
        
        r = self.m_clock_name(pnext)
        if r == None:
            return None
        pnext, clock_name = r
        clock_names.append(clock_name)
        
        while True:
            pnext = self.m_zmsp(pnext)

            if self.s[pnext] != ',':
                break
            pnext += 1
            
            pnext = self.m_zmsp(pnext)

            r = self.m_clock_name(pnext)
            if r == None:
                return None
            pnext, clock_name = r
            clock_names.append(clock_name)
    
        pnext = self.m_zmsp(pnext)
        print pnext

        comment = ''
        r = self.m_comment(pnext)
        if r != None:
            pnext, comment = r
            print pnext
            print "comment =", comment

        r = self.m_newline(pnext)
        if r == None:
            return None
        pnext = r
        print "NEWLINE"
        print pnext
        
        return pnext, clock_names
        
