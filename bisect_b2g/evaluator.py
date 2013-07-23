import os
import logging
import tempfile
import subprocess

from bisect_b2g.util import run_cmd


log = logging.getLogger(__name__)


def script_evaluator(script, history):
    log.debug("Running evaluator with %s", script)
    rc = run_cmd(command=script, rc_only=True)
    log.debug("Script returned %d", rc)
    return rc == 0


def interactive_evaluator(history):
    # STEPS:
    # 1. create env with PS1
    # 2. create bash script file with good and bad programs
    # 3. start bash using $SHELL and including the BASH_ENV from 2.
    # 4. Return True if RC=69 and False if RC=96
    # Improvments:
    #   * history bash command to show which changesets are already dismissed
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
    env = dict(os.environ)
    env['PS1'] = "BISECT: $ "
    env['PS2'] = "> "
    env['IGNOREEOF'] = str(1024*4)
    tmpfd, tmpn = tempfile.mkstemp()
    os.write(tmpfd, rcfile)
    os.close(tmpfd)

    rc = subprocess.call([os.environ['SHELL'], "--rcfile", tmpn, "--noprofile"], env=env)

    if os.path.exists(tmpn):
        os.unlink(tmpn)

    if rc == 69:
        rv = True
    elif rc == 96:
        rv = False
    elif rc == 0:
        log.warning("Received an exit command from interactive console, exiting bisection completely")
        sys.exit(1)
    else:
        raise Exception("An unexpected exit code '%d' occured in the interactive prompt" % rc)
    log.debug("Interactive evaluator returned %d", rc)
    return rv

