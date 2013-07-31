#!/usr/bin/env python

import os
import stat
import unittest
import subprocess
import tempfile

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
        expected_output = "I am dumb\n"
        command = [dumbo, 'STDOUT:' + expected_output]
        actual_output = util.run_cmd(command)[1]
        # XXX: Figure out why I need to strip the output!
        self.assertEqual(
            expected_output + '\n',
            actual_output,
            "'%s' != '%s'" % (expected_output, actual_output))

    def test_rc_only(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        command = [dumbo, "STDOUT:Hello", "STDERR:Bye", "--exit-code"]
        exit_code = 69
        rv = util.run_cmd(command + [str(exit_code)], rc_only=True)
        self.assertEqual(exit_code, rv[0])
        rv = util.run_cmd(command + [str(exit_code + 1)], rc_only=True)
        self.assertNotEqual(exit_code, rv[0])
        self.assertEqual(None, rv[1])

    def test_inc_err(self):
        self.assertTrue(os.access(dumbo, os.R_OK | os.X_OK))
        command_with_stderr = [
            dumbo, "STDOUT:stdout", "STDERR:stderr", "STDOUT:stdout"
        ]
        output = util.run_cmd(command_with_stderr, inc_err=True)
        self.assertEqual(
            'stdout\nstderr\nstdout\n',
            output[1]
        )
        output = util.run_cmd(command_with_stderr, inc_err=False)
        self.assertEqual(
            'stdout\nstdout\n',
            output[1]
        )

    def test_workdir(self):
        real_workdir = subprocess.check_output(['pwd', '-P']).strip()
        self.assertEqual(real_workdir, os.getcwd())
        code, output = util.run_cmd(['pwd', '-P'], workdir=os.getcwd())
        self.assertEqual(os.getcwd() + '\n', output)
        tmpdir = tempfile.mkdtemp(prefix=__file__)
        code, output = util.run_cmd(['pwd', '-P'], workdir=tmpdir)
        self.assertEqual(tmpdir + '\n', output)
        os.rmdir(tmpdir)

    def test_stupidity(self):
        self.assertRaises(
            util.RunCommandException,
            util.run_cmd,
            ([dumbo, "STDOUT:stdout", "STDERR:stderr"]),
            **{'inc_err': True, 'rc_only': True}
        )
