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

    def oldest(l):
        """Find the oldest head of a linked list and return it"""
        if len(l) == 1:
            log.debug("There was only one item to evaluate, returning %s", l[0])
            return l[0]
        else:
            oldest = l[0]
            for other in l[1:]:
                if other.date < oldest.date:
                    oldest = other
            log.debug("Found oldest: %s", oldest)
            return oldest

    def create_line(prev, new):
        log.debug("prev: %s", prev)
        log.debug("new:  %s", new)
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        if len(new) == 1:
            # If we're done finding the oldest, we want to make a new line then
            # move the list of the oldest one forward
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
            # Otherwise, we want to recurse to finding the oldest objects
            o = oldest(new)
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





