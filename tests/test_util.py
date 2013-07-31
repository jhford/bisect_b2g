#!/usr/bin/env python

import os
import stat
import unittest

import bisect_b2g.util as util

dumbo = os.path.abspath(os.path.join(os.path.split(__file__)[0], 'dumbo.py'))


def compare_dicts(dict1, dict2):
    for key in set(dict1.keys() + dict2.keys()):
        if key not in dict1 or key not in dict2:
            return False
        if dict1[key] != dict2[key]:
            return False
    return True


class TestEnvironmentGeneration(unittest.TestCase):

    def setUp(self):
        self.real_env = dict(os.environ)

    def test_no_add_or_delete(self):
        gen_env = util.generate_env()
        self.assertTrue(compare_dicts(self.real_env, gen_env))

    def test_add_var(self):
        key = 'TESTING123'
        value = key + 'VALUE'
        self.assertFalse(key in self.real_env)
        env_addition = {key: value}
        gen_env = util.generate_env(env=env_addition)
        self.real_env[key] = value
        self.assertTrue(compare_dicts(self.real_env, gen_env))

    def test_overwrite_var(self):
        key = 'HOME'
        value = 'INVALID'
        self.assertTrue(key in self.real_env)
        env_addition = {key: value}
        gen_env = util.generate_env(env=env_addition)
        self.real_env[key] = value
        self.assertTrue(compare_dicts(self.real_env, gen_env))

    def test_del_var(self):
        key = 'HOME'
        self.assertTrue(key in self.real_env)
        gen_env = util.generate_env(delete_env=[key])
        del self.real_env[key]
        self.assertTrue(compare_dicts(self.real_env, gen_env))

    def test_add_and_del_var(self):
        add_key = 'TESTING123'
        value = add_key + 'VALUE'
        del_key = 'HOME'
        self.assertTrue(del_key in self.real_env)
        self.assertFalse(add_key in self.real_env)
        env_addition = {add_key: value}
        gen_env = util.generate_env(env=env_addition, delete_env=[del_key])
        del self.real_env[del_key]
        self.real_env[add_key] = value
        self.assertTrue(compare_dicts(self.real_env, gen_env))

    def test_add_and_del_same_var(self):
        add_key = 'HOME'
        value = add_key + 'VALUE'
        del_key = 'HOME'
        self.assertTrue(del_key in self.real_env)
        self.assertTrue(add_key in self.real_env)
        env_addition = {add_key: value}
        gen_env = util.generate_env(env=env_addition, delete_env=[del_key])
        del self.real_env[del_key]
        self.assertTrue(compare_dicts(self.real_env, gen_env))


class RunCmdTest(unittest.TestCase):

    def setUp(self):
        os.chmod(dumbo, stat.S_IXUSR | stat.S_IRUSR)

    def test_default(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        expected_output = "I am dumb"
        command = [dumbo, expected_output]
        actual_output = util.run_cmd(command)
        # XXX: Figure out why I need to strip the output!
        self.assertEqual(
            expected_output.strip(),
            actual_output.strip(),
            "'%s' != '%s'" % (expected_output, actual_output))

    def test_rc_only(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        exit_code = 69
        rc = util.run_cmd([dumbo, "--exit-code", str(exit_code), "Hello"],
                          rc_only=True)
        self.assertEqual(exit_code, rc)
        rc = util.run_cmd([dumbo, "--exit-code", str(exit_code+1), "Hello"],
                          rc_only=True)
        self.assertNotEqual(exit_code, rc)

    def test_ignore_err(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        command_with_stderr = [
            dumbo, "STDOUT:stdout", "STDERR:stderr", "STDOUT:stdout"
        ]
        output = util.run_cmd(command_with_stderr, inc_err=False,
                              ignore_err=True)
        self.assertEqual(
            'stdout\nstdout\n',
            output
        )

    def test_inc_err(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        command_with_stderr = [
            dumbo, "STDOUT:stdout", "STDERR:stderr", "STDOUT:stdout"
        ]
        output = util.run_cmd(command_with_stderr, inc_err=True,
                              ignore_err=False)
        self.assertEqual(
            'stdout\nstderr\nstdout\n',
            output
        )

    def test_stupidity(self):
        self.assertRaises(
            Exception,
            util.run_cmd,
            ([dumbo, "STDOUT:stdout", "STDERR:stderr"]),
            {'inc_err': True, 'ignore_err': True}
        )
