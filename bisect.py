#!/usr/bin/env python

import json
import sys
import os
import subprocess as sp
import shutil
from optparse import OptionParser
import math

import isodate

# Store global options.  Probably a bad idea
global_options = {}

devnull = open(os.devnull, 'w+')

def run_cmd(command, workdir=os.getcwd(), read_out=True, inc_err=False,
            ignore_err=True, env=None, delete_env=False, rc_only=False, **kwargs):
    """ Wrap subprocess in a way that I like.
    command: string or list of the command to run
    workdir: directory to do the work in
    inc_err: include stderr in the output string returned
    read_out: decide whether we're going to want output returned or printed
    env: add this dictionary to the default environment
    delete_env: delete these environment keys
    rc_only: run the command, ignore output"""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    if delete_env:
        for d in delete_env:
            if full_env.has_key(d):
                del full_env[d]
    if inc_err and ignore_err:
        raise Exception("You are trying to include *and* ignore stderr, wtf?")
    elif inc_err:
        kwargs = kwargs.copy()
        kwargs['stderr'] = sp.STDOUT
    elif ignore_err:
        kwargs = kwargs.copy()
        kwargs['stderr'] = sp.PIPE # This might be a bad idea, research this!
    if rc_only:
        func = sp.call
        # This probably leaves a bunch of wasted open file handles.  Meh
        kwargs['stderr'] = kwargs['stdout'] = devnull
    elif read_out:
        func = sp.check_output
    else:
        func = sp.check_call
    #print "command: %s, workdir=%s" % (command, workdir)
    return func(command, cwd=workdir, env=full_env, **kwargs)


class Repository(object):

    def __init__(self, name, url):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = os.path.join(os.getcwd(), "repos", self.name)
        print "Initializing %s at '%s'" % (self.name, self.local_path)



    def sanitize(self):
        assert 0

    def update(self):
        assert 0

    def clone(self):
        assert 0

    def init_repo(self):
        assert 0

    def get_rev(self):
        assert 0

    def set_rev(self, rev):
        assert 0

    def rev_list(self, branch, start, end):
        assert 0


class GitRepository(Repository):

    def __init__(self, *args):
        Repository.__init__(self, *args)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            self.update()
        else:
            self.clone()

    def clone(self):
        local_path_base = os.path.split(self.local_path)[0]
        if not os.path.exists(local_path_base):
            os.makedirs(local_path_base)
        run_cmd(["git", "clone", self.url, self.local_path])

    def update(self):
        # self.set_rev('master') # TODO THIS IS A HACK!
        run_cmd(["git", "fetch", "--all"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["git", "rev-parse", "HEAD"])

    def set_rev(self, rev):
        # This will create a detached head
        run_cmd(["git", "checkout", rev], workdir=self.local_path)

    def rev_list(self, start, end):
        def fix_git_timestamp(timestamp):
            """Yay git for generating non-ISO8601 datetime stamps.  Git generates, e.g.
            2013-01-29 16:06:52 -0800 but ISO8601 would be 2013-01-29T16:06:52-0800"""
            as_list = list(timestamp)
            as_list[10] = 'T'
            del as_list[19]
            return "".join(as_list)
        sep = " --- "
        command = ["git", "log"]
        if global_options['follow_merges']:
            command.append("--first-parent")
        command.extend(["--date-order", "%s..%s" % (start, end),
                        '--pretty=%%H%s%%ci' % sep])
        raw_output = run_cmd(command, self.local_path )
        intermediate_output = [x.strip() for x in raw_output.split('\n')]
        output = []
        for line in [x for x in intermediate_output if x != '']:
            h,s,d = line.partition(sep)
            output.append((h, isodate.parse_datetime(fix_git_timestamp(d))))
        return output

        
class HgRepository(Repository):

    def __init__(self, *args):
        Repository.__init__(self, *args)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            self.update()
        else:
            self.clone()

    def clone(self):
        run_cmd(["hg", "clone", self.url, self.local_path])

    def update(self):
        run_cmd(["hg", "pull", "-u"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["hg", "identify"])

    def set_rev(self, rev):
        run_cmd(["hg", "update", "--rev", rev], workdir=self.local_path)

    def rev_list(self, start, end):
        assert 0

class Project(object):

    def __init__(self, name, url, branch, good, bad, vcs="git"):
        object.__init__(self)
        self.name = name
        self.url = url
        self.branch = branch
        self.good = good
        self.bad = bad
        self.vcs = vcs

        if self.vcs == 'git':
            repocls = GitRepository
        elif self.vcs == 'hg':
            repocls = HgRepository
        else:
            print >> sys.stderr, "ERROR: Unsupported repository type"
            exit(1)
        self.repository = repocls(self.name, self.url)

    def rev_list(self):
        if not hasattr(self, 'last_rl_id') or self.last_rl_id != (self.good, self.bad):
            self.last_rl_id = (self.good, self.bad)
            self.last_rl = self.repository.rev_list(self.good, self.bad)
        return self.last_rl

    def __str__(self):
        return "Name: %(name)s, Url: %(url)s, Branch: %(branch)s, Good: %(good)s, Bad: %(bad)s, VCS: %(vcs)s" % self.__dict__
    __repr__ = __str__


class Rev(object):

    def __init__(self, h, prj, date):
        object.__init__(self)
        self.h = h
        self.prj = prj
        self.date = date

    def __str__(self):
        return "%s, %s, %s" % (self.h, self.prj.name, self.date)
    __repr__=__str__


class N(object):

    def __init__(self, data, n):
        object.__init__(self)
        self.data = data
        self.n = n

    def __str__(self):
        return 'self: %s, next: %s, data: %s' % (id(self), id(self.n), str(self.data))
    __repr__ = __str__


def make_ll(l):
    """ Make a linked list such that l[0] is the first item is the list head returned"""
    rl = reversed(l[:])
    head = None
    for i in rl:
        head = N(i, head)
    return head


def print_ll(l):
    """ Print out a linked list"""
    i=l
    while i != None:
        print i.data
        i=i.n


def build_history(projects):
    global_rev_list = []
    rev_lists = []
    last_revs = []
    for project in projects:
        rev_lists.append(make_ll([Rev(x[0], project, x[1]) for x in project.rev_list()]))

    def oldest(l):
        """Find the oldest head of a linked list and return it"""
        if len(l) == 1:
            return l[0]
        else:
            oldest = l[0]
            for other in l[1:]:
                if other.data.date > oldest.data.date:
                    oldest = other
            return oldest

    def create_line(prev, new):
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        if len(new) == 1:
            # If we're done finding the oldest, we want to make a new line then
            # move the list of the oldest one forward
            global_rev_list.append([x.data for x in prev + new])
            #line = []
            #for x in prev + new:
            #    line.append(x.data)
            #global_rev_list.append(line)
            rli = rev_lists.index(new[0])
            if rev_lists[rli].n == None:
                last_revs.append(rev_lists[rli])
                del rev_lists[rli]
            else:
                rev_lists[rli] = rev_lists[rli].n
            return
        else:
            # Otherwise, we want to recurse to finding the oldest objects
            o = oldest(new)
            if not o in prev:
                prev.append(o)
            del new[new.index(o)]
            create_line(prev, new)
            


    while len(rev_lists) > 0:
        create_line(last_revs[:], rev_lists[:])

    return global_rev_list
    

def bisect(history, script, all_history, num=0):
    middle = len(history) / 2
    if len(history) == 1:
        return history[0]
    else:
        cur = history[middle]
        total = round(math.log(len(all_history) + len(all_history) % 2, 2))
        print "Running test %d of %d or %d: " % (num+1, total - 1, total)
        for rev in cur:
            print "  * %s@%s" % (rev.prj.name, rev.h)
        for rev in cur:
            rev.prj.repository.set_rev(rev.h)
        rc = run_cmd(command=script, rc_only=True)

        if rc == 0:
            return bisect(history[middle:], script, all_history, num+1)
        else:
            return bisect(history[:middle], script, all_history, num+1)


def main():
    projects = []
    parser = OptionParser("%prog - I bisect gecko and gaia!")
    # There should be an option for a script that figures out if a given pairing is
    # good or bad
    parser.add_option("--script", "-x", help="Script to run.  Return code 0 \
                      means the current changesets are good, Return code 1 means \
                      that it's bad", dest="script")
    parser.add_option("--follow-merges", help="Should git/hg log functions \
                      follow both sides of a merge or only the mainline.\
                      This equates to --first-parent in git log",
                      dest="follow_merges", default=True, action="store_false")
    opts, args = parser.parse_args()

    class InvalidArg(exception): pass
    
    def parse_arg(arg):
        arg_data = {}
        uri_sep = '@'
        rev_sep = '..'
        uri, x, rev_range = arg.partition(uri_sep)
        if x != uri_sep:
            raise InvalidArg("Argument '%s' is not properly formed" % arg)
        arg_data['good'], x, arg_data['bad'] = rev_range.partition(rev_sep)
        if x != rev_sep:
            raise InvalidArg("Argument '%s' is not properly formed" % arg)
        
        if os.path.exists(uri):
            print "Path exists, reusing"
            arg_data['local_path'] = uri
            arg_data['uri'] = uri
        else:
            pass # Here's where we 




    # ARG FORMAT: URI@GOOD..BAD
    for arg in args:


    
    global_options['follow_merges'] = opts.follow_merges

    for i in project_names:
        project = Project(name=i,
                          url=getattr(opts, "%s_url"%i),
                          branch=getattr(opts, "%s_branch"%i),
                          good=getattr(opts, "good_%s"%i),
                          bad=getattr(opts, "bad_%s"%i),
                          vcs=getattr(opts, "vcs_%s"%i))
        projects.append(project)

    combined_history = build_history(projects)
    found = bisect(combined_history, opts.script, combined_history)
    print "="*80
    print "Found:"
    for rev in found:
        print "  * %s@%s" % (rev.prj.name, rev.h)
    print "This was revision pair %d of %d total revision pairs" % \
    (combined_history.index(found), len(combined_history))


if __name__ == "__main__":
    main()
