import sys
import os
import logging
import math


from bisect_b2g.repository import Project, Rev


log = logging.getLogger(__name__)


def build_history(projects):
    global_rev_list = []
    last_revs = []
    rev_lists = [x.rev_ll() for x in projects]

    def newest(l):
        """Find the newest head of a linked list and return it"""
        if len(l) == 1:
            log.debug("There was only one item to evaluate, returning %s", l[0])
            return l[0]
        else:
            newest = l[0]
            for other in l[1:]:
                if other.date > newest.date:
                    newest = other
            log.debug("Found newest: %s", newest)
            return newest

    def create_line(prev, new):
        log.debug("prev: %s", prev)
        log.debug("new:  %s", new)
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        if len(new) == 1:
            # If we're done finding the newest, we want to make a new line then
            # move the list of the newest one forward
            global_rev_list.append(sorted(prev + new, key=lambda x: x.prj.name))
            rli = rev_lists.index(new[0])
            if rev_lists[rli].next_rev == None:
                log.debug("Found the last revision for %s", rev_lists[rli].prj.name)
                last_revs.append(rev_lists[rli])
                del rev_lists[rli]
            else:
                log.debug("Moving pointer for %s forward", rev_lists[rli].prj.name)
                rev_lists[rli] = rev_lists[rli].next_rev
            return
        else:
            # Otherwise, we want to recurse to finding the newest objects
            o = newest(new)
            if not o in prev:
                prev.append(o)
            del new[new.index(o)]
            log.debug("Building a line, %.2f%% complete ", float(len(prev)) / ( float(len(prev) + len(new))) * 100)
            create_line(prev, new)

    while len(rev_lists) > 0:
        create_line(last_revs[:], rev_lists[:])

    log.debug("Global History:")
    map(log.debug, global_rev_list)
    return global_rev_list


def validate_history(history):
    pass


def dump_history(projects, history, filename):
    tree = ET.ElementTree()
    root = ET.Element('history')
    root.text = '\n'
    root.tail = '\n'
    tree._setroot(root)
    for prj in projects:
        p = ET.SubElement(root, 'project')
        p.set('name', prj.name)
        p.set('good', prj.good)
        p.set('bad', prj.bad)
        p.tail = '\n'
    for line in history:
        l = ET.SubElement(root, 'line')
        l.text = '\n  '
        l.tail = '\n'
        for rev in sorted(line, key=lambda x: x.prj.name):
            r = ET.SubElement(l, rev.prj.name)
            r.set('commit', rev.hash)
            r.set('date', isodate.datetime_isoformat(rev.date))
            r.tail = '\n  '
        r.tail = '\n'
    
    return tree.write(filename)


