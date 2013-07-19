import sys
import os
import logging
import math

from bisect_b2g.repository import Project, Rev


log = logging.getLogger(__name__)


class N(object):

    def __init__(self, data, n):
        object.__init__(self)
        self.data = data
        self.n = n

    def __str__(self):
        return str(self.data)
    __repr__ = __str__


def make_ll(l):
    """ Make a linked list such that l[0] is the first item is the list head returned"""
    rl = reversed(l[:])
    head = None

    for i in rl:
        head = N(i, head)

    return head


def build_history(projects):
    global_rev_list = []
    rev_lists = []
    last_revs = []
    for project in projects:
        rev_lists.append(make_ll([Rev(x[0], project, x[1]) for x in project.rev_list()]))

    def oldest(l):
        """Find the oldest head of a linked list and return it"""
        if len(l) == 1:
            log.debug("There was only one item to evaluate, returning %s", l[0].data)
            return l[0]
        else:
            oldest = l[0]
            for other in l[1:]:
                if other.data.date > oldest.data.date:
                    oldest = other
            log.debug("Found oldest: %s", oldest.data)
            return oldest

    def create_line(prev, new):
        log.debug("prev: %s", prev)
        log.debug("new:  %s", new)
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        if len(new) == 1:
            # If we're done finding the oldest, we want to make a new line then
            # move the list of the oldest one forward
            global_rev_list.append([x.data for x in prev + new])
            rli = rev_lists.index(new[0])
            if rev_lists[rli].n == None:
                log.debug("Found the last revision for %s", rev_lists[rli].data.prj.name)
                last_revs.append(rev_lists[rli])
                del rev_lists[rli]
            else:
                log.debug("Moving pointer for %s forward", rev_lists[rli].data.prj.name)
                rev_lists[rli] = rev_lists[rli].n
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


def _bisect(history, evaluator, max_recur, num):
    log.info('-' * 80)
    middle = len(history) / 2
    if len(history) == 1:
        log.debug("Found commit: %s", history[0])
        return history[0]
    else:
        cur = history[middle]
        log.info("Running test %d of %d or %d: ", num + 1, max_recur - 1, max_recur)
        map(log.info, ["  * %s@%s" % (rev.prj.name, rev.h) for rev in cur])
        for rev in cur:
            log.debug("Setting revisions for %s", rev)
            rev.prj.set_rev(rev.h)
        outcome = evaluator(cur)

        if outcome:
            log.info("Test passed")
            return _bisect(history[middle:], evaluator, max_recur, num+1)
        else:
            log.info("Test failed")
            return _bisect(history[:middle], evaluator, max_recur, num+1)


# Make the first entry into the function a little tidier
def bisect(history, evaluator):
    max_recur = round(math.log(len(history) + len(history) % 2, 2))
    return _bisect(history, evaluator, max_recur, 0)

