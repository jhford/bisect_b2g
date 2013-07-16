#!/usr/bin/env python

import json
import sys
import os
import subprocess as sp
import shutil
from optparse import OptionParser
import isodate

class Repository(object):

    def __init__(self, name, url):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = os.path.join(os.getcwd(), "repos", self.name)

    def run_cmd(self, command, workdir=os.getcwd(), read_out=True, inc_err=False, ignore_err=True, env=None, delete_env=False, **kwargs):
        """ Wrap subprocess in a way that I like.
        command: string or list of the command to run
        workdir: directory to do the work in
        inc_err: include stderr in the output string returned
        read_out: decide whether we're going to want output returned or printed
        env: add this dictionary to the default environment
        delete_env: delete these environment keys"""
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
        if read_out:
            func = sp.check_output
        else:
            func = sp.check_call
        print "command: %s, workdir=%s" % (command, workdir)
        return func(command, cwd=workdir, env=full_env, **kwargs)

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
        self.run_cmd(["git", "clone", self.url, self.local_path])

    def update(self):
        self.run_cmd(["git", "pull", "--all"], workdir=self.local_path)

    def get_rev(self):
        return self.run_cmd(["git", "rev-parse", "HEAD"])

    def set_rev(self, rev):
        # This will create a detached head
        self.run_cmd(["git", "checkout", rev], workdir=self.local_path)

    def rev_list(self, start, end):
        def fix_git_timestamp(timestamp):
            """Yay git for generating non-ISO8601 datetime stamps.  Git generates, e.g.
            2013-01-29 16:06:52 -0800 but ISO8601 would be 2013-01-29T16:06:52-0800"""
            as_list = list(timestamp)
            as_list[10] = 'T'
            del as_list[19]
            return "".join(as_list)
        sep = " --- "
        raw_output = self.run_cmd(["git", "log", "--first-parent", "--reverse", "%s..%s" % (start, end), '--pretty="%%H%s%%ci"' % sep], self.local_path )
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
        self.run_cmd(["hg", "clone", self.url, self.local_path])

    def update(self):
        self.run_cmd(["hg", "pull", "-u"], workdir=self.local_path)

    def get_rev(self):
        return self.run_cmd(["hg", "identify"])

    def set_rev(self, rev):
        self.run_cmd(["hg", "update", "--rev", rev], workdir=self.local_path)

    def rev_list(self, start, end):
        pass

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


class N(object):

    def __init__(self, data, n):
        object.__init__(self)
        self.data = data
        self.n = n

    def __str__(self):
        return "%s, %s, %s" % (self.data[0][0], self.data[0][1],
                               self.data[1].name)
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
        rev_lists.append(make_ll([(x,project) for x in project.rev_list()]))

    def oldest(l):
        """Find the oldest head of a linked list and return it"""
        if len(l) == 1:
            return l[0]
        else:
            oldest = l[0]
            for other in l[1:]:
                if other.data[1] > oldest.data[1]:
                    oldest = other
            return oldest

    def create_line(prev, new):
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        print 'PREV: %s, NEW: %s' % (prev,new)
        if len(new) == 1:
            # If we're done finding the oldest, we want to make a new line then
            # move the list of the oldest one forward
            global_rev_list.append(tuple(prev+new))
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

    print "GLOBAL LIST:\n  *", "\n  * ".join([str(x) for x in
                                             global_rev_list]), '\n\n\n'
    return global_rev_list
    

def bisect(history):
    print "Doing a bisect!"
    pass


def main():
    project_names = ('gaia', 'gecko')
    projects = []
    parser = OptionParser("%prog - I bisect gecko and gaia!")
    # There should be an option for a script that figures out if a given pairing is
    # good or bad
    for i in project_names:
        parser.add_option("--%s-url" % i, help="URL to use for cloning %s" % i,
                          dest="%s_url" % i)
        parser.add_option("--%s-branch" % i, help="Branch to use for %s" % i,
                          dest="%s_branch" % i)
        parser.add_option("--good-%s" % i, help="Good commit/changeset for %s" % i,
                          dest="good_%s" % i)
        parser.add_option("--bad-%s" % i, help="Bad commit/changeset for %s" % i,
                          dest="bad_%s" % i)
        parser.add_option("--%s-vcs" % i, help="Which VCS to use for %s" % i,
                          dest="vcs_%s" % i, default="hg" if i == 'gecko' else "git")
    opts, args = parser.parse_args()
    bad_opts = []
    for option in ('gaia_url', 'gaia_branch', 'good_gaia', 'bad_gaia', 'vcs_gaia', \
                   'gecko_url', 'gecko_branch', 'good_gecko', 'bad_gecko', 'vcs_gecko'):
        if not getattr(opts, option):
            bad_opts.append(option)
    if len(bad_opts) > 0:
        parser.print_help()
        print "ERROR: You have some bad options: '%s'" % "', '".join(bad_opts)
        parser.exit(1)

    for i in project_names:
        project = Project(name=i,
                          url=getattr(opts, "%s_url"%i),
                          branch=getattr(opts, "%s_branch"%i),
                          good=getattr(opts, "good_%s"%i),
                          bad=getattr(opts, "bad_%s"%i),
                          vcs=getattr(opts, "vcs_%s"%i))
        projects.append(project)

    combined_history = build_history(projects)
    bisect(combined_history)


if __name__ == "__main__":
    main()
