import os
import sys
import logging
import tempfile
import subprocess

from bisect_b2g.util import run_cmd


log = logging.getLogger(__name__)


class EvaluatorError(Exception):
    pass


class Evaluator(object):

    def __init__(self):
        object.__init__(self)

    def eval(self, history_line):
        assert 0, "Unimplemented"


class ScriptEvaluator(Evaluator):

    def __init__(self, script):
        Evaluator.__init__(self)
        self.script = script

    def eval(self, history_line):
        log.debug("Running script evaluator with %s", self.script)
        code, output = run_cmd(command=self.script, rc_only=True)
        log.debug("Script evaluator returned %d", code)
        return code == 0


class InteractiveEvaluator(Evaluator):

    def __init__(self):
        Evaluator.__init__(self)

    def generate_script(self):
        rcfile = """
        echo
        echo "To mark a changeset, type either 'good' or 'bad'"
        echo

        function good () {
            exit 69
        }

        function bad () {
            exit 96
        }

        """
        tmpfd, tmpn = tempfile.mkstemp()
        os.write(tmpfd, rcfile)
        os.close(tmpfd)
        return tmpn



    def eval(self, history_line):
        # STEPS:
        # 1. create env with PS1
        # 2. create bash script file with good and bad programs
        # 3. start bash using $SHELL and including the BASH_ENV from 2.
        # 4. Return True if RC=69 and False if RC=96
        # Improvments:
        #   * history bash command to show which changesets are dismissed
        rcfile = self.generate_script()
        env = dict(os.environ)
        env['PS1'] = "BISECT: $ "
        env['PS2'] = "> "
        env['IGNOREEOF'] = str(1024*4)

        # We don't use run_cmd here because that function uses
        # subprocess.Popen.communicate, which wait()s for the
        # process before displaying output.  That doesn't work
        # here because we're doing "smart" things here
        code = subprocess.call(
            [os.environ['SHELL'], "--rcfile", rcfile, "--noprofile"],
            env=env, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)

        if os.path.exists(rcfile):
            os.unlink(rcfile)

        if code == 69:
            rv = True
        elif code == 96:
            rv = False
        elif code == 0:
            log.warning("Received an exit command from interactive " +
                        " console, exiting bisection completely")
            exit(1)
        else:
            raise EvaluatorError("An unexpected exit code '%d' occured in" +
                                 "the interactive prompt" % code)
        log.debug("Interactive evaluator returned %d", code)
        return rv


def script_evaluator(script, history):
    log.debug("Running evaluator with %s", script)
    rc, output = run_cmd(command=script, rc_only=True)
    log.debug("Script returned %d", rc)
    return rc == 0
