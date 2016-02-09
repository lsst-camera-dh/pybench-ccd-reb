#
# Grammar for the REB3 sequencer language
# (sequencer with variables)
#
# Author: Laurent Le Guillou

import re

class SeqParser(object):

    #-----------------------------------------------------------------------

    # ZMSP :== [ \t]* # zero or more spaces
    _p_zmsp = "([ \t]*)"

    # OMSP :== [ \t]+ # one or more spaces
    _p_omsp = "([ \t]+)"

    # NEWLINE :== (\n | \r\n | \r) # newline
    _p_newline = "(\n|\r\n|\r)"

    # COMMENT :== '#' .*  [until NEWLINE]
    # _p_comment = "\#(\.*)$"
    _p_comment = "#(.*)"
    
    # INTEGER ::= [0-9]+
    _p_integer = "(\d+)"

    # NAME ::= [A-Za-z][0-9A-Za-z\_]*
    _p_name = "([A-Za-z][\dA-Za-z\_]*)"
    
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

    #-----------------------------------------------------------------------
    # ZMSP :== [ \t]* # zero or more spaces
    # OMSP :== [ \t]+ # one or more spaces

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
    # NEWLINE :== (\n | \r\n | \r)
    _p_newline = "(\n|\r\n|\r)"

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

        return (pnext, comment)

    #-----------------------------------------------------------------------
    # EMPTY_LINE ::= SPACE? COMMENT? NEWLINE

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
        number = int(matches.group(1))
        pnext = pos + l

        return (pnext, number)

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
    # XXX_SECTION_MARKER = "[XXX]" SPACE? COMMENT? NEWLINE

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
            
        
    #-----------------------------------------------------------------------
    # CLOCK_NAME ::= NAME
    # CLOCK_ID   ::= INTEGER
    # CLOCK_DEF_LINE  ::=
    #       SPACE? CLOCK_NAME SPACE? ':' CLOCK_ID SPACE? COMMENT? NEWLINE
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
        
        return (pnext, clock_name, clock_id)
    
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
                pnext, clock_def = r[0], (r[1], r[2])
                clock_defs.append(clock_def)
                continue

            break

        return (pnext, clock_defs)
                
    #-----------------------------------------------------------------------

