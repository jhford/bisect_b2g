#!/bin/false

import os
import subprocess
import logging
import select

log = logging.getLogger(__name__)

devnull = open(os.devnull, 'w+')


def generate_env(env=None, delete_env=None):
    full_env = dict(os.environ)

    if env:
        full_env.update(env)

    if delete_env:
        for d in delete_env:
            if d in full_env:
                del full_env[d]
    return full_env


class RunCommandException(Exception):
    pass


# XXX: This function is garbage!  It should have a complete rewrite
def run_cmd(command, workdir=os.getcwd(), inc_err=False,
            env=None, delete_env=False, rc_only=False,
            raise_if_not=0, **kwargs):

    kwargs = kwargs.copy()
    full_env = generate_env(env, delete_env)

    if rc_only and inc_err:
        raise RunCommandException(
            "You're asking to ignore output(rc_only) but to " +
            "include stderr.  You are quizzical"
        )

    if rc_only:
        kwargs['stdout'] = kwargs['stderr'] = devnull

    if inc_err:
        kwargs['stderr'] = subprocess.STDOUT
    else:
        kwargs['stderr'] = devnull

    for x in ('stdout', 'stderr'):
        if not x in kwargs:
            kwargs[x] = subprocess.PIPE

    proc = subprocess.Popen(command, cwd=workdir, env=full_env, **kwargs)

    output, stderr = proc.communicate()

    exit_code = proc.poll()
    if raise_if_not is None or exit_code == raise_if_not or rc_only:
        return exit_code, output
    else:
        raise RunCommandException(
            "Exit code is %d, not %d for %s" % (exit_code,
                                                raise_if_not,
                                                command)
        )
