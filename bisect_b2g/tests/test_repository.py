import unittest
import os
import shutil
import tempfile

import datetime
import pytz

from bisect_b2g.util import run_cmd
from bisect_b2g.repository import GitRepository, HgRepository


def make_temp_dir(prefix):
    dir = os.path.join(os.getcwd(), '.test_repos')
    #raise Exception(dir)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return tempfile.mkdtemp(prefix=prefix+'_', dir=dir)


class TempGitRepository(object):

    def __init__(self, revision_names=[], data_f='file'):
        object.__init__(self)
        self.revision_names = revision_names
        self.revisions = []
        self.location = loc = make_temp_dir('TempGit')
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


class TempHgRepository(object):

    def __init__(self, revision_names=[], data_f='file'):
        object.__init__(self)
        self.revision_names = revision_names
        self.revisions = []
        self.location = loc = make_temp_dir('TempHg')
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
            # HG Creates a complete commit for tags.  Lolwut?
            #run_cmd(['hg', 'tag', str(r_name)], workdir=loc)
            commit = run_cmd(['hg', 'log', '-l1', '--template', "{node}", "."],
                             workdir=loc)[1].strip()
            self.revisions.append(
                {'name': str(r_name), 'commit': commit,
                 'date': date})


class BaseRepositoryFixture(object):
    def setUp(self):
        self.t_repo = self.fake_cls(revision_names=[
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])
        self.repo = self.real_cls(name="Testing", url=self.t_repo.location,
                                  local_path=self.t_repo.location)

    def tearDown(self):
        shutil.rmtree(self.t_repo.location)

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

    def compare_rev_lists(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        commits_to_assert = ([], [])
        dates_to_assert = ([], [])

        for rev in range(max(len(expected), len(actual))):
            commits_to_assert[0].append(expected[rev]['commit'])
            commits_to_assert[1].append(actual[rev][0])

            dates_to_assert[0].append((
                expected[rev]['date'].ctime(),
                expected[rev]['date'].utcoffset()))
            dates_to_assert[1].append((
                actual[rev][1].ctime(),
                actual[rev][1].utcoffset()))

        self.assertEqual(*commits_to_assert)
        self.assertEqual(*dates_to_assert)

    def test_simple_rev_list(self):
        a_rev_list = self.repo.rev_list(
            self.t_repo.revisions[0]['commit'],
            self.t_repo.revisions[-1]['commit']
        )
        revs = self.t_repo.revisions

        self.compare_rev_lists(revs, a_rev_list)


class GitTests(object):
    fake_cls = TempGitRepository
    real_cls = GitRepository
    heady_thing = 'HEAD'


class HgTests(object):
    fake_cls = TempHgRepository
    real_cls = HgRepository
    heady_thing = '.'


class GitRepositoryTests(GitTests, BaseRepositoryFixture, unittest.TestCase):
    pass


class HgRepositoryTests(HgTests, BaseRepositoryFixture, unittest.TestCase):

    # We do this here because in HG tags are just part of a file that's
    # normally tracked and not as it's own object type.  This makes our tests
    # confused because the repository ends up having more commits than we want
    # for testing
    def tag_repo(self):
        for i in self.t_repo.revisions:
            run_cmd(['hg', 'tag', str(i['name']), '-r',
                    str(i['commit'])], workdir=self.t_repo.location)

    @unittest.skip("Skipping because implementation is bad")
    def test_resolve_tag_by_tag(self):
        pass

    @unittest.skip("Skipping because implementation is bad")
    def test_resolve_tag_by_commit(self):
        pass

    @unittest.skip("Skipping because implementation is bad")
    def test_resolve_tag_by_default(self):
        pass

    def test_get_rev_by_tag(self):
        self.tag_repo()
        BaseRepositoryFixture.test_get_rev_by_tag(self)

    def test_set_rev_by_tag(self):
        self.tag_repo()
        BaseRepositoryFixture.test_set_rev_by_tag(self)
