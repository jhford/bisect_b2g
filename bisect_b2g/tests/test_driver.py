#!/usr/bin/env python

import unittest
import os

import bisect_b2g.driver as driver


class SimpleFunctionTests(unittest.TestCase):

    def test_local_path_to_name(self):
        local_file = os.path.join(os.getcwd(), 'test_file_name')
        self.assertEqual(
            driver.local_path_to_name(local_file),
            os.path.split(local_file)[1]
        )
        local_file_with_git = local_file + '.git'
        self.assertEqual(
            driver.local_path_to_name(local_file_with_git),
            os.path.split(local_file)[1]
        )

    def test_uri_to_name(self):
        name = 'test'
        uri = "git://github.com/sample/%s" % name
        self.assertEqual(
            driver.uri_to_name(uri),
            name
        )
        self.assertEqual(
            driver.uri_to_name(uri + '.git'),
            name
        )
        sshish_uri = 'github.com:%s' % name
        self.assertEqual(
            driver.uri_to_name(sshish_uri),
            name
        )
        sshish_uri = 'github.com:%s.git' % name
        self.assertEqual(
            driver.uri_to_name(sshish_uri),
            name
        )


def comp_dict(a, b):
    for i in set(a.keys() + b.keys()):
        if a[i] != b[i]:
            return False
    return True


class ArgTests(unittest.TestCase):

    def setUp(self):
        self.full_arg_data = {
            'local_path': os.path.abspath(os.path.join('repos', 'local_path')),
            'uri': 'github.com:sample/remote_name',
            'name': 'local_path',
            'vcs': 'git',
            'good': 'abc1234',
            'bad': '1234abc',
        }

        self.full_arg = driver.make_arg(self.full_arg_data)

        self.simple_arg_data = self.full_arg_data.copy()
        self.simple_arg_data['uri'] = self.simple_arg_data['local_path']
        self.simple_arg = driver.make_arg(self.simple_arg_data)


class MakeArgTests(ArgTests):

    def test_make_arg_no_uri(self):
        simple_arg = driver.make_arg(self.simple_arg_data)
        self.assertEqual(
            simple_arg,
            "GIT%(local_path)s@%(good)s..%(bad)s" % self.simple_arg_data
        )

    def test_make_arg_with_uri(self):
        full_arg = driver.make_arg(self.full_arg_data)
        self.assertEqual(
            full_arg,
            "GIT%(uri)s->%(local_path)s@%(good)s..%(bad)s" % self.full_arg_data
        )

    def test_make_arg_with_invalid_name(self):
        # Let's make some bogus arg_data
        self.full_arg_data['name'] = 'something-invalid'
        self.assertRaises(driver.InvalidArg,
                          driver.make_arg,
                          self.full_arg_data)

    def test_make_arg_with_invalid_vcs(self):
        self.full_arg_data['vcs'] = 'something-invalid'
        self.assertRaises(driver.InvalidArg,
                          driver.make_arg,
                          self.full_arg_data)


class ParseArgTests(ArgTests):

    def test_parse_arg_no_uri(self):
        out_data = driver.parse_arg(self.simple_arg)
        self.assertTrue(comp_dict(self.simple_arg_data, out_data))

    def test_parse_arg_with_uri(self):
        out_data = driver.parse_arg(self.full_arg)
        self.assertTrue(comp_dict(self.full_arg_data, out_data))

    def test_parse_arg_guess_vcs(self):
        git_urls = ('github.com:foo/bar.git', 'git://github.com:foo/bar.git',
                    'git://github.com:foo/bar')
        hg_urls = ('https://hg.mozilla.org/foo',)
        urls = [(x, 'git') for x in git_urls]
        urls.extend([(x, 'hg') for x in hg_urls])
        for uri, expected in urls:
            out_data = driver.parse_arg('%s->bar@good..bad' % uri)
            self.assertEqual(
                expected,
                out_data['vcs'],
                uri + ' ' + expected + "!=" + out_data['vcs'])

    def test_parse_arg_ambiguous_argument(self):
        bad_uri = 'https://zombo.com/test->notspecific@good..bad'
        self.assertRaises(driver.InvalidArg,
                          driver.parse_arg,
                          (bad_uri))

    def test_parse_arg_with_conflicting_vcs_clues(self):
        bad_uri = \
            'github.comhg.mozilla.org/mozilla-central->notspecific@good..bad'
        self.assertRaises(driver.InvalidArg,
                          driver.parse_arg,
                          (bad_uri))

    def test_parse_arg_git_prefix_with_hg_server(self):
        bad_uri = 'git://hg.mozilla.org/mozilla-central->notspecific@good..bad'
        self.assertRaises(driver.InvalidArg,
                          driver.parse_arg,
                          (bad_uri))
