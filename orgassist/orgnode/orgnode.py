"""
The Orgnode module consists of the Orgnode class for representing a
headline and associated text from an org-mode file, and routines for
constructing data structures of these classes.

LICENSE:

Copyright (c) 2012 Albin Stjerna, Takafumi Arakaki, and Charles Cave

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

https://github.com/albins/orgnode.git

"""

import re
import datetime
import codecs


def get_datetime(year, month, day, hour=None, minute=None, second=None):
    if "" in (year, month, day):
        raise ValueError ("First three arguments must not contain empty str")
    if None in (year, month, day):
        raise ValueError ("First three arguments must not contain None")

    ymdhms = []
    for a in [year, month, day, hour, minute, second]:
        if a != None and a != "":
            ymdhms.append(int(a))

    if len(ymdhms) > 3:
        return datetime.datetime(*ymdhms)
    else:
        return datetime.date(*ymdhms)

def _re_compile_date():
    """
    >>> re_date = _re_compile_date()
    >>> re_date.match('')
    >>> m = re_date.match('<2010-06-21 Mon>')
    >>> m.group()
    '<2010-06-21 Mon>'
    >>> m.group(1)
    >>> m.group(16)
    '<2010-06-21 Mon>'
    >>> m = re_date.match('<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>')
    >>> m.group()
    '<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>'
    >>> m.group(1)
    '<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>'
    >>> m.group(16)
    """
    date_pattern = "<(\d+)\-(\d+)\-(\d+)([^>\d]*)((\d+)\:(\d+))?>"
    re_date = re.compile('(%(dtp)s--%(dtp)s)|(%(dtp)s)'
                         % dict(dtp=date_pattern))
    return re_date

_RE_DATE = _re_compile_date()
def find_daterangelist(string):
    datelist = []
    rangelist = []
    for dm in _RE_DATE.findall(string):
        if dm[0]:
            d1 = get_datetime(dm[1], dm[2], dm[3], dm[6], dm[7])
            d2 = get_datetime(dm[8], dm[9], dm[10], dm[13], dm[14])
            rangelist.append((d1, d2))
        else:
            dt = get_datetime(dm[16], dm[17], dm[18], dm[21], dm[22])
            datelist.append(dt)
    return (datelist, rangelist)

_RE_SCHEDULED = re.compile(
    'SCHEDULED:\s+<(\d+)\-(\d+)\-(\d+)[^>\d]*((\d+)\:(\d+))?>')
def find_scheduled(line):
    """
    Find SCHEDULED from given string.
    Return datetime object if found else None.
    """
    sd_re = _RE_SCHEDULED.search(line)
    if sd_re:
        if sd_re.group(4) == None:
            sched_date = datetime.date(int(sd_re.group(1)),
                                       int(sd_re.group(2)),
                                       int(sd_re.group(3)) )
        else:
            sched_date = datetime.datetime(int(sd_re.group(1)),
                                           int(sd_re.group(2)),
                                           int(sd_re.group(3)),
                                           int(sd_re.group(5)),
                                           int(sd_re.group(6)) )
    else:
        sched_date = None
    return sched_date

_RE_DEADLINE = re.compile(
    'DEADLINE:\s+<(\d+)\-(\d+)\-(\d+)[^>\d]*((\d+)\:(\d+))?>')
def find_deadline(line):
    """
    Find DEADLINE from given string.
    Return datetime object if found else None.
    """
    dd_re = _RE_DEADLINE.search(line)
    if dd_re:
        if dd_re.group(4) == None:
            deadline_date = datetime.date(int(dd_re.group(1)),
                                          int(dd_re.group(2)),
                                          int(dd_re.group(3)) )
        else:
            deadline_date = datetime.datetime(int(dd_re.group(1)),
                                              int(dd_re.group(2)),
                                              int(dd_re.group(3)),
                                              int(dd_re.group(5)),
                                              int(dd_re.group(6)) )
    else:
        deadline_date = None
    return deadline_date

_RE_TAGSRCH = re.compile('(.*?)\s*:(.*?):(.*?)$')
def find_tags_and_heading(heading):
    """
    Get first tag, all tags, and heading without tags.
    This is helper function of makelist.
    """
    tag1 = ""
    alltags = set() # set of all tags in headline
    tagsrch = _RE_TAGSRCH.search(heading)
    if tagsrch:
        heading = tagsrch.group(1)
        tag1 = tagsrch.group(2)
        alltags.add(tag1)
        tag2 = tagsrch.group(3)
        if tag2:
            alltags |= set(tag2.split(':')) - set([''])
    return (tag1, alltags, heading)

_RE_PROP_SRCH = re.compile('^\s*:(.*?):\s*(.*?)\s*$')
def find_property(line):
    """
    Find property from given string.
    Return (key, value)-pair if found else (None, None).
    """
    prop_key = None
    prop_val = None
    prop_srch = _RE_PROP_SRCH.search(line)
    if prop_srch:
        prop_key = prop_srch.group(1)
        prop_val = prop_srch.group(2)
        if prop_key == 'Effort':
            if ":" in prop_val:
                (h, m) = prop_val.split(":", 2)
            else:
                h, m = prop_val, "0"
            if h.isdigit() and m.isdigit():
                prop_val = int(h)*60 + int(m)
    return (prop_key, prop_val)


_RE_CLOSED = re.compile(
    'CLOSED:\s+\[(\d+)\-(\d+)\-(\d+)[^\]\d]*((\d+)\:(\d+))?\]')
def find_closed(line):
    """
    Find CLOSED from given string.
    Return datetime object if found else None.
    """
    cl_re = _RE_CLOSED.search(line)
    if cl_re:
        if cl_re.group(4) == None:
            closed_date = datetime.date(int(cl_re.group(1)),
                                        int(cl_re.group(2)),
                                        int(cl_re.group(3)) )
        else:
            closed_date = datetime.datetime(int(cl_re.group(1)),
                                            int(cl_re.group(2)),
                                            int(cl_re.group(3)),
                                            int(cl_re.group(5)),
                                            int(cl_re.group(6)) )
    else:
        closed_date = None
    return closed_date


_RE_CLOCK = re.compile(
    'CLOCK:\s+'
    '\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]--'
    '\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]\s+=>\s+(\d+)\:(\d+)'
    )
def find_clock(line):
    """
    Find CLOCK from given string.
    Return three tuple (start, stop, length) which is datetime object
    of start time, datetime object of stop time and length in minute.
    """
    match = _RE_CLOCK.search(line)
    if match is None:
        return None
    groups = [int(d) for d in match.groups()]
    ymdhm1 = groups[:5]
    ymdhm2 = groups[5:10]
    hm3 = groups[10:]
    return (
        datetime.datetime(*ymdhm1),
        datetime.datetime(*ymdhm2),
        hm3[0]*60 + hm3[1],
        )

_RE_HEADING = re.compile('^(\*+)\s(.*?)\s*$')
_RE_TODO_KWDS = re.compile(' ([A-Z][A-Z0-9]+)\(?')
_RE_TODO_SRCH = re.compile('^\s*([A-Z][A-Z0-9]+)\s(.*?)$')
_RE_PRTY_SRCH = re.compile('^\[\#(A|B|C)\] (.*?)$')

def makelist(filename, todo_default=['TODO', 'DONE']):
    """
    Read an org-mode file and return a list of Orgnode objects
    created from this file.
    """
    ctr = 0

    f = codecs.open(filename, 'r', 'utf8')

    todos = set(todo_default) # populated from #+SEQ_TODO line
    level         = ''
    heading       = ""
    bodytext      = ""
    tag1          = ""      # The first tag enclosed in ::
    alltags       = set([]) # set of all tags in headline
    sched_date    = ''
    deadline_date = ''
    closed_date   = ''
    clocklist     = []
    datelist      = []
    rangelist     = []
    nodelist      = []
    propdict      = dict()

    for line in f:
        ctr += 1
        hdng = _RE_HEADING.search(line)

        if hdng:
            if heading:  # we are processing a heading line
                thisNode = Orgnode(level, heading, bodytext, tag1, alltags)
                if sched_date:
                    thisNode.setScheduled(sched_date)
                    sched_date = ""
                if deadline_date:
                    thisNode.setDeadline(deadline_date)
                    deadline_date = ''
                if closed_date:
                    thisNode.setClosed(closed_date)
                    closed_date = ''
                if clocklist:
                    thisNode.setClock(clocklist)
                    clocklist = []
                if datelist:
                    thisNode.setDateList(datelist)
                    datelist = []
                if rangelist:
                    thisNode.setRangeList(rangelist)
                    rangelist = []
                thisNode.setProperties(propdict)
                nodelist.append( thisNode )
                propdict = dict()
            level = hdng.group(1)
            heading =  hdng.group(2)
            bodytext = ""
            (tag1, alltags, heading) = find_tags_and_heading(heading)
        else:      # we are processing a non-heading line
            if line.startswith('#+SEQ_TODO'):
                todos |= set(_RE_TODO_KWDS.findall(line))
                continue
            if line.find(':PROPERTIES:') >= 0: continue
            if line.find(':END:') >= 0: continue
            (prop_key, prop_val) = find_property(line)
            if prop_key:
                propdict[prop_key] = prop_val
                continue
            _sched_date = find_scheduled(line)
            _deadline_date = find_deadline(line)
            _closed_date = find_closed(line)
            sched_date = _sched_date or sched_date
            deadline_date = _deadline_date or deadline_date
            closed_date = closed_date or _closed_date
            if not _sched_date and not _deadline_date:
                (dl, rl) = find_daterangelist(line)
                datelist += dl
                rangelist += rl
            clock = find_clock(line)
            if clock:
                clocklist.append(clock)
            if not (line.startswith('#') or _sched_date or _deadline_date
                    or clock or _closed_date):
                bodytext = bodytext + line

    # write out last node
    thisNode = Orgnode(level, heading, bodytext, tag1, alltags)
    thisNode.setProperties(propdict)
    if sched_date:
        thisNode.setScheduled(sched_date)
    if deadline_date:
        thisNode.setDeadline(deadline_date)
    if closed_date:
        thisNode.setClosed(closed_date)
        closed_date = ''
    if clocklist:
        thisNode.setClock(clocklist)
        clocklist = []
    if datelist:
        thisNode.setDateList(datelist)
        datelist = []
    if rangelist:
        thisNode.setRangeList(rangelist)
        rangelist = []
    nodelist.append( thisNode )

    # using the list of TODO keywords found in the file
    # process the headings searching for TODO keywords
    for n in nodelist:
        h = n.Heading()

        todoSrch = _RE_TODO_SRCH.search(h)

        if todoSrch:
            if todoSrch.group(1) in todos:
                n.setHeading( todoSrch.group(2) )
                n.setTodo ( todoSrch.group(1) )
        prtysrch = _RE_PRTY_SRCH.search(n.Heading())
        if prtysrch:
            n.setPriority(prtysrch.group(1))
            n.setHeading(prtysrch.group(2))

    # set parent of nodes
    ancestors = [None]
    n1 = nodelist[0]
    l1 = n1.Level()
    for n2 in nodelist:
        # n1, l1: previous node and its level
        # n2, l2: this node and its level
        l2 = n2.Level()
        if l1 < l2:
            ancestors.append(n1)
        else:
            while len(ancestors) > l2:
                ancestors.pop()
        if ancestors:
            n2.setParent(ancestors[-1])
        n1 = n2
        l1 = l2

    return nodelist

######################
class Orgnode(object):
    """
    Orgnode class represents a headline, tags and text associated
    with the headline.
    """
    def __init__(self, level, headline, body, tag, alltags):
        """
        Create an Orgnode object given the parameters of level (as the
        raw asterisks), headline text (including the TODO tag), and
        first tag. The makelist routine postprocesses the list to
        identify TODO tags and updates headline and todo fields.
        """
        self.level = len(level)
        self.headline = headline
        self.body = body
        self.tag = tag            # The first tag in the list
        self.tags = set(alltags)  # All tags in the headline
        self.todo = ""
        self.prty = ""            # empty of A, B or C
        self.scheduled = ""       # Scheduled date
        self.deadline = ""        # Deadline date
        self.clock = []
        self.closed = ""
        self.properties = dict()
        self.datelist = []
        self.rangelist = []
        self.parent = None

        # Look for priority in headline and transfer to prty field

    def Heading(self):
        """
        Return the Heading text of the node without the TODO tag
        """
        return self.headline

    def setHeading(self, newhdng):
        """
        Change the heading to the supplied string
        """
        self.headline = newhdng

    def Body(self):
        """
        Returns all lines of text of the body of this node except the
        Property Drawer
        """
        return self.body

    def Level(self):
        """
        Returns an integer corresponding to the level of the node.
        Top level (one asterisk) has a level of 1.
        """
        return self.level

    def Priority(self):
        """
        Returns the priority of this headline: 'A', 'B', 'C' or empty
        string if priority has not been set.
        """
        return self.prty

    def setPriority(self, newprty):
        """
        Change the value of the priority of this headline.
        Values values are '', 'A', 'B', 'C'
        """
        self.prty = newprty

    def Tag(self):
        """
        Returns the value of the first tag.
        For example, :HOME:COMPUTER: would return HOME
        """
        return self.tag

    def Tags(self, inher=False):
        """
        Returns a list of all tags
        For example, :HOME:COMPUTER: would return ['HOME', 'COMPUTER']
        If `inher` is True, then all tags from ancestors is included.
        """
        if inher and self.parent:
            return self.tags | set(self.parent.Tags(True))
        else:
            return self.tags

    def hasTag(self, srch):
        """
        Returns True if the supplied tag is present in this headline
        For example, hasTag('COMPUTER') on headling containing
        :HOME:COMPUTER: would return True.
        """
        return srch in self.tags

    def setTag(self, newtag):
        """
        Change the value of the first tag to the supplied string
        """
        self.tag = newtag

    def setTags(self, taglist):
        """
        Store all the tags found in the headline. The first tag will
        also be stored as if the setTag method was called.
        """
        self.tags |= set(taglist)

    def Todo(self):
        """
        Return the value of the TODO tag
        """
        return self.todo

    def setTodo(self, value):
        """
        Set the value of the TODO tag to the supplied string
        """
        self.todo = value

    def setProperties(self, dictval):
        """
        Sets all properties using the supplied dictionary of
        name/value pairs
        """
        self.properties = dictval

    def Properties(self):
        """
        Return the value of the properties.
        """
        return self.properties

    def Property(self, keyval):
        """
        Returns the value of the requested property or null if the
        property does not exist.
        """
        return self.properties.get(keyval, "")

    def setScheduled(self, dateval):
        """
        Set the scheduled date using the supplied date object
        """
        self.scheduled = dateval

    def Scheduled(self):
        """
        Return the scheduled date object or null if nonexistent
        """
        return self.scheduled

    def setDeadline(self, dateval):
        """
        Set the deadline (due) date using the supplied date object
        """
        self.deadline = dateval

    def Deadline(self):
        """
        Return the deadline date object or null if nonexistent
        """
        return self.deadline

    def setDateList(self, datelist):
        """
        Set the list of date using list of the supplied date object
        """
        self.datelist = datelist[:]

    def DateList(self):
        """
        Return the list of all date as date object
        """
        return self.datelist[:]

    def setRangeList(self, rangelist):
        """
        Set the list of date range using list of the supplied timedelta object
        """
        self.rangelist = rangelist[:]

    def RangeList(self):
        """
        Return the list of all date as date object
        """
        return self.rangelist[:]

    def hasDate(self):
        return (bool(self.scheduled) or
                bool(self.deadline) or
                bool(self.datelist) or
                bool(self.rangelist) )

    def setClosed(self, closed):
        """
        Set the closed date using the supplied date object
        """
        self.closed = closed

    def Closed(self):
        """
        Return closed time as datetime object or empty string if nonexistent.
        """
        return self.closed

    def setClock(self, clock):
        """
        Set the list of clocked time using list of three tuple
        (start, stop, length) which is datetime object of start time,
        datetime object of stop time and length in minute.
        """
        self.clock = clock[:]

    def Clock(self):
        """
        Return list of clocked time (tuple of (start, stop, length))
        """
        return self.clock

    def setParent(self, parent):
        """
        Set parent node
        """
        self.parent = parent

    def Parent(self):
        """
        Return parent node if exist else None.
        """
        return self.parent

    def Root(self):
        """
        Return root node

        What is root node?::

          * I am node A, a root node       <- Root node!
          ** I am a child of node A
          ** I am a child of node A too
          * I am also a root node            <- Root node!

        """
        child = self
        while True:
            parent = child.Parent()
            if parent is None:
                return child
            child = parent

    def __repr__(self):
        """
        Print the level, heading text and tag of a node and the body
        text as used to construct the node.
        """
        # This method is not completed yet.
        n = ''
        for i in range(0, self.level):
            n = n + '*'
        n = n + ' ' + self.todo + ' '
        if self.prty:
            n = n +  '[#' + self.prty + '] '
        n = n + repr(self.headline)
        n = "%-60s " % n     # hack - tags will start in column 62
        closecolon = ''
        for t in sorted(self.tags):
            n = n + ':' + t
            closecolon = ':'
        n = n + closecolon
# Need to output Scheduled Date, Deadline Date, property tags The
# following will output the text used to construct the object
        n = n + "\n" + repr(self.body)

        return n
