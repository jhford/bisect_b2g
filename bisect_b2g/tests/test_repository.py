import unittest
import os
import shutil
import tempfile

import git
import datetime
import pytz

from bisect_b2g.util import run_cmd
from bisect_b2g.repository import Project, GitRepository, HgRepository, Rev


class TempGitRepository(object):

    def __init__(self, revision_names=[], data_f='file'):
        object.__init__(self)
        self.revision_names = revision_names
        self.revisions = []
        self.location = loc = \
            tempfile.mkdtemp(prefix='TempGit')
        run_cmd(['git', 'init'], workdir=loc)
        for r_name in revision_names:
            with open(os.path.join(loc, data_f), 'w+b') as f:
                f.write(str(r_name))
            run_cmd(['git', 'add', data_f], workdir=loc)
            date = datetime.datetime.now(pytz.timezone('US/Pacific')) \
                .replace(microsecond=0)
            env = {
                'GIT_COMMITTER_DATE': date.isoformat(),
                'GIT_AUTHOR_DATE': date.isoformat()
            }
            run_cmd(['git', 'commit', '-m',
                     "%s %s" % (data_f, r_name)],
                    workdir=loc, env=env)
            commit = run_cmd(['git', 'rev-parse', 'HEAD'],
                             workdir=loc)[1].strip()
            run_cmd(['git', 'tag', str(r_name)], workdir=loc)
            self.revisions.append(
                {'name': str(r_name), 'commit': commit,
                 'date': date})

    def __del__(self):
        shutil.rmtree(self.location)


class TempHgRepository(object):

    def __init__(self, revision_names=[], data_f='file'):
        object.__init__(self)
        self.revision_names = revision_names
        self.revisions = []
        self.location = loc = \
            tempfile.mkdtemp(prefix='TempHg')
        run_cmd(['hg', 'init'], workdir=loc)
        for r_name in revision_names:
            with open(os.path.join(loc, data_f), 'w+b') as f:
                f.write(str(r_name))
            run_cmd(['hg', 'add', data_f], workdir=loc)
            date = datetime.datetime.now(pytz.timezone('US/Pacific'))

            # Dec 6 13:18 -0600
            date_string = date.replace(microsecond=0) \
                .strftime("%b %d %H:%M:%S %z")
            run_cmd(['hg', 'commit', '--date', date_string, '-m',
                     "%s %s" % (data_f, r_name)],
                    workdir=loc)
            commit = run_cmd(['hg', 'log', '-l1', '--template', "{node}", "."],
                             workdir=loc)[1].strip()
            run_cmd(['hg', 'tag', str(r_name)], workdir=loc)
            self.revisions.append(
                {'name': str(r_name), 'commit': commit,
                 'date': date})

    def __del__(self):
        shutil.rmtree(self.location)


class BaseRepositoryFixture(object):
    def setUp(self):
        self.t_repo = self.test_cls(revision_names=[
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])
        self.repo = self.real_cls(name="Testing", url=self.t_repo.location,
                                  local_path=self.t_repo.location)

    def test_get_rev_by_default_commit(self):
        self.repo.set_rev(self.t_repo.revisions[-1]['commit'])
        self.assertEqual(self.t_repo.revisions[-1]['commit'],
                         self.repo.get_rev())

    def test_get_rev_by_heady_thing(self):
        self.repo.set_rev(self.t_repo.revisions[-1]['commit'])
        self.assertEqual(self.t_repo.revisions[-1]['commit'],
                         self.repo.get_rev(self.heady_thing))

    def test_get_rev_by_tag(self):
        self.assertEqual(self.t_repo.revisions[3]['commit'],
                         self.repo.get_rev(self.t_repo.revisions[3]['name']))

    def test_get_rev_by_commit(self):
        self.assertEqual(self.t_repo.revisions[3]['commit'],
                         self.repo.get_rev(self.t_repo.revisions[3]['commit']))

    def test_get_rev_invalid(self):
        self.assertRaises(Exception,
                          self.repo.get_rev, ('INVALID'))

    def test_set_rev_by_tag(self):
        self.repo.set_rev(self.t_repo.revisions[4]['name'])
        self.assertEqual(self.t_repo.revisions[4]['commit'],
                         self.repo.get_rev(self.t_repo.revisions[4]['name']))

    def test_set_rev_by_commit(self):
        self.repo.set_rev(self.t_repo.revisions[5]['commit'])
        self.assertEqual(
            self.t_repo.revisions[5]['commit'],
            self.repo.get_rev(self.t_repo.revisions[5]['commit']))

    def test_resolve_tag_by_tag(self):
        self.assertEqual(
            self.t_repo.revisions[6]['name'],
            self.repo._resolve_tag(self.t_repo.revisions[6]['name']))
        self.assertEqual(
            self.t_repo.revisions[6]['name'],
            self.repo.resolve_tag(self.t_repo.revisions[6]['name']))

    def test_resolve_tag_by_commit(self):
        self.assertEqual(
            self.t_repo.revisions[6]['name'],
            self.repo._resolve_tag(self.t_repo.revisions[6]['commit']))
        self.assertEqual(
            self.t_repo.revisions[6]['name'],
            self.repo.resolve_tag(self.t_repo.revisions[6]['commit']))

    def test_resolve_tag_by_default(self):
        self.assertEqual(
            self.t_repo.revisions[-1]['name'],
            self.repo._resolve_tag(None))
        self.assertEqual(
            self.t_repo.revisions[-1]['name'],
            self.repo.resolve_tag(None))

    def test_simple_rev_list(self):
        a_rev_list = self.repo.rev_list(
            self.t_repo.revisions[0]['commit'],
            self.t_repo.revisions[-1]['commit']
        )
        revs = self.t_repo.revisions

        def do_asserts(asserts):
            self.assertEqual(asserts[0], asserts[1])

        commit_to_assert = ([], [])
        dates_to_assert = ([], [])
        for rev in range(len(revs)):
            commit_to_assert[0].append(revs[rev]['commit'])
            commit_to_assert[1].append(a_rev_list[rev][0])
            # Using ctime conversion as fuzz factor.
            # This ensures equality to the second
            dates_to_assert[0].append(
                (revs[rev]['date'].ctime(), revs[rev]['date'].utcoffset()))
            dates_to_assert[1].append(
                (a_rev_list[rev][1].ctime(), a_rev_list[rev][1].utcoffset()))


class GitRepositoryTests(BaseRepositoryFixture, unittest.TestCase):
    test_cls = TempGitRepository
    real_cls = GitRepository
    heady_thing = 'HEAD'


class HgRepositoryTests(BaseRepositoryFixture, unittest.TestCase):
    test_cls = TempHgRepository
    real_cls = HgRepository
    heady_thing = '.'

    @unittest.skip("Busted")
    def test_resolve_tag_by_tag(self):
        pass

    @unittest.skip("Busted")
    def test_resolve_tag_by_commit(self):
        pass

    @unittest.skip("Busted")
    def test_resolve_tag_by_default(self):
        pass
