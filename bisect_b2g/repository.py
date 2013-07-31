import os
import logging
from xml.etree import ElementTree
import datetime

import isodate
import git

from bisect_b2g.util import run_cmd
import git.exc as gitexc

log = logging.getLogger(__name__)


class Repository(object):

    def __init__(self, name, url, local_path, follow_merges=False):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = local_path
        self.follow_merges = follow_merges
        self.resolved_tags = {}
        if url == local_path:
            log.info("Setting up %s", local_path)
        else:
            log.info("Setting up %s->%s", url, local_path)

    def sanitize(self):
        assert 0

    def clone(self):
        assert 0

    def init_repo(self):
        assert 0

    def get_rev(self, rev=None):
        assert 0

    def set_rev(self, rev):
        assert 0

    def resolve_tag(self, rev=None):
        if not rev is None and not rev in self.resolved_tags:
            self.resolved_tags[rev] = self._resolve_tag(rev)
        return self.resolved_tags[rev]

    def _resolve_tag(self, rev=None):
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
            self.repo = git.Repo(self.local_path)
        else:
            log.debug("%s does not exist, cloning", self.name)
            self.clone()

    def clone(self):
        self.repo = git.Repo.clone_from(self.url, self.local_path)

    def get_rev(self, rev=None):
        return self.repo.commit(rev if rev else 'HEAD').hexsha

    def set_rev(self, rev):
        self.resolve_tag(rev)
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.git.checkout(rev)
        log.debug("Set %s to %s", self.local_path, rev)
        log.debug("Intended to set %s, actually set %s",
                  rev, self.get_rev())

    def _resolve_tag(self, rev=None):
        git = self.repo.git
        _rev = rev[:]
        try:
            _rev = git.describe(rev, tags=True, exact_match=True)
        except gitexc.GitCommandError:
            pass
        return _rev

    def validate_rev(self, rev):
        pass

    def rev_list(self, start, end):

        start_parents = self.repo.commit(start).parents
        if len(start_parents) == 0:
            rev_spec = end
        else:
            rev_spec = '%s^..%s' % (start, end)

        commits = self.repo.iter_commits(rev=rev_spec,
                                         first_parent=True)

        output = []

        class FixedSecondsOffset(datetime.tzinfo):
            def __init__(self, offset):
                self.offset = offset

            def utcoffset(self, dt):
                return datetime.timedelta(seconds=-self.offset)

            def tzname(self, dt):
                return ''

            def dst(self, dt):
                return datetime.timedelta(0)

        for commit in commits:
            output.append((
                commit.hexsha,
                datetime.datetime.fromtimestamp(
                    commit.committed_date,
                    FixedSecondsOffset(commit.committer_tz_offset))
            ))
        output.reverse()
        return output


class HgRepository(Repository):

    def __init__(self, *args, **kwargs):
        Repository.__init__(self, *args, **kwargs)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            pass
        else:
            self.clone()

    def clone(self):
        run_cmd(["hg", "clone", self.url, self.local_path])

    def get_rev(self, rev=None):
        return run_cmd(["hg", "log", "-l1", "--template", "{node}",
                        "-r", rev if rev else "."],
                       workdir=self.local_path)[1].strip()

    def set_rev(self, rev):
        run_cmd(["hg", "update", "-C", "--rev", rev], workdir=self.local_path)

    def validate_rev(self, rev):
        assert 0

    def _resolve_tag(self, rev=None):
        log.debug("HG Tag resolution is unimplmenented, return input")
        return rev

    def rev_list(self, start, end):
        log.debug("Fetching HG revision list for %s..%s", start, end)
        command = ["hg", "log", "-r", "%s..%s" % (start, end),
                   "--style", "xml"]

        raw_xml = run_cmd(command, self.local_path)[1].strip()
        root = ElementTree.XML(raw_xml)
        output = []

        for log_entry in root.findall('logentry'):
            d = isodate.parse_datetime(log_entry.find('date').text)
            h = log_entry.get('node')
            output.append((h, d))

        return output


class Project(object):
    def __init__(self, name, url, local_path, good, bad,
                 vcs="git", follow_merges=False):
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
            raise Exception("Unsupported repository type")

        log.debug("Using %s for %s", str(repocls), self.name)

        self.repository = repocls(self.name,
                                  self.url,
                                  self.local_path,
                                  follow_merges=self.follow_merges)

    def rev_ll(self):
        rev_list = reversed(self.repository.rev_list(self.good, self.bad))
        head = None

        for h, date in rev_list:
            head = Rev(h, self, date, head)

        return head

    def set_rev(self, rev):
        return self.repository.set_rev(rev)

    def resolve_tag(self, rev=None):
        return self.repository.resolve_tag(rev)

    def __str__(self):
        return "Name: %(name)s, Url: %(url)s, " % (self.__dict__,) + \
               "Good: %(good)s, Bad: %(bad)s, VCS: %(vcs)s" % self.__dict__
    __repr__ = __str__


class Rev(object):

    def __init__(self, hash, prj, date, next_rev=None):
        object.__init__(self)
        self.hash = hash
        self.prj = prj
        self.date = date
        self.next_rev = next_rev

    def tag(self):
        return self.prj.resolve_tag(self.hash)

    def __str__(self):
        return "%s@%s" % (self.prj.name, self.hash)
    __repr__ = __str__
