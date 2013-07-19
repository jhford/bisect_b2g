import os
import logging
from xml.etree import ElementTree

import isodate

from bisect_b2g.util import run_cmd

log = logging.getLogger(__name__)

class Repository(object):

    def __init__(self, name, url, local_path, follow_merges=False):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = local_path
        self.follow_merges = follow_merges
        log.info("Setting up %s", name if name == local_path else "%s at %s" % (name, local_path))

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

    def validate_rev(self, rev):
        assert 0

    def rev_list(self, start, end):
        assert 0


class GitRepository(Repository):

    def __init__(self, *args, **kwargs):
        Repository.__init__(self, *args, **kwargs)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            log.debug("%s already exists, updating", self.name)
            self.update()
        else:
            log.debug("%s does not exist, cloning", self.name)
            self.clone()

    def clone(self):
        local_path_base = os.path.split(self.local_path)[0]

        if not os.path.exists(local_path_base) and local_path_base != '':
            os.makedirs(local_path_base)

        run_cmd(["git", "clone", self.url, self.local_path])

    def update(self):
        # Assuming here that all fetches go over the network
        pass#run_cmd(["git", "fetch", "--all"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["git", "rev-parse", "HEAD"], workdir=self.local_path).strip()

    def set_rev(self, rev):
        # This will create a detached head
        run_cmd(["git", "reset", "--hard", "HEAD"], workdir=self.local_path)
        run_cmd(["git", "checkout", rev], workdir=self.local_path)
        log.debug("Set %s to %s", self.local_path, rev)

    def validate_rev(self, rev):
        pass

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

        if not self.follow_merges:
            command.append("--first-parent")

        command.extend(["--date-order", "%s..%s" % (start, end),
                        '--pretty=%%H%s%%ci' % sep])
        raw_output = run_cmd(command, self.local_path)
        intermediate_output = [x.strip() for x in raw_output.split('\n')]
        output = []

        for line in [x for x in intermediate_output if x != '']:
            h,s,d = line.partition(sep)
            output.append((h, isodate.parse_datetime(fix_git_timestamp(d))))

        return output


class HgRepository(Repository):

    def __init__(self, *args, **kwargs):
        Repository.__init__(self, *args, **kwargs)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            self.update()
        else:
            self.clone()

    def clone(self):
        run_cmd(["hg", "clone", self.url, self.local_path])

    def update(self):
        run_cmd(["hg", "pull", "-u"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["hg", "log", "-l1", "--template", "{node}"], workdir=self.local_path).strip()

    def set_rev(self, rev):
        run_cmd(["hg", "update", "-C", "--rev", rev], workdir=self.local_path)

    def validate_rev(self, rev):
        assert 0

    def rev_list(self, start, end):
        # HG is a pain in the butt.  For good..bad,
        # we need to hg up -r good ; hg log -r bad.
        log.debug("Fetching HG revision list for %s..%s", start, end)
        sep = " --- "
        template = "{node}%s{date}" % sep
        old_rev = self.get_rev()
        self.set_rev(start)
        command = ["hg", "log", "-r", end, "--style", "xml"]

        raw_xml = run_cmd(command, self.local_path).strip()
        root = ElementTree.XML(raw_xml)
        output = []

        for log_entry in root.findall('logentry'):
            d = isodate.parse_datetime(log_entry.find('date').text)
            h = log_entry.get('node')
            output.append((h, d))
        
        self.set_rev(old_rev)

        return output


class Project(object):

    def __init__(self, name, url, local_path, good, bad, vcs="git", follow_merges=False):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = local_path
        self.good = good
        self.bad = bad
        self.vcs = vcs
        self.follow_merges = follow_merges

        if self.vcs == 'git':
            repocls = GitRepository
        elif self.vcs == 'hg':
            repocls = HgRepository
        else:
            log.error("Unsupported repository type")
            exit(1)
        
        log.debug("Using %s for %s", str(repocls), self.name)
        
        self.repository = repocls(self.name, self.url, self.local_path, follow_merges=self.follow_merges)

    def rev_ll(self):
        rev_list = reversed(self.repository.rev_list(self.good, self.bad))
        head = None    
    
        for h, date in rev_list:
            head = Rev(h, self, date, head)

        return head

    def set_rev(self, rev):
        return self.repository.set_rev(rev)

    def __str__(self):
        return "Name: %(name)s, Url: %(url)s, Good: %(good)s, Bad: %(bad)s, VCS: %(vcs)s" % self.__dict__
    __repr__ = __str__


class Rev(object):

    def __init__(self, hash, prj, date, next_rev=None):
        object.__init__(self)
        self.hash = hash
        self.prj = prj
        self.date = date
        self.next_rev = next_rev

    def __str__(self):
        return "%s@%s" % (self.prj.name, self.hash)
    __repr__=__str__

