#!/bin/false

import os
import subprocess
import logging

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


# XXX: This function is garbage!  It should have a complete rewrite
def run_cmd(command, workdir=os.getcwd(), read_out=True, inc_err=False,
            ignore_err=True, env=None, delete_env=False, rc_only=False,
            **kwargs):
    """ Wrap subprocess in a way that I like.
    command: string or list of the command to run
    workdir: directory to do the work in
    inc_err: include stderr in the output string returned
    read_out: decide whether we're going to want output returned or printed
    env: add this dictionary to the default environment
    delete_env: delete these environment keys
    rc_only: run the command, ignore output"""

    full_env = generate_env(env, delete_env)

    kwargs = kwargs.copy()
    if inc_err and ignore_err:
        raise Exception("You are trying to include *and* ignore stderr, wtf?")
    elif ignore_err or rc_only:
        # This might be a bad idea, research this!
        kwargs['stderr'] = devnull
    elif inc_err:
        kwargs['stderr'] = subprocess.STDOUT

    if rc_only:
        func = subprocess.call
    elif read_out:
        func = subprocess.check_output
    else:
        func = subprocess.check_call

    log.debug("command=%s, workdir=%s, env=%s, kwargs=%s",
              command, workdir, env or {}, kwargs)

    return func(command, cwd=workdir, env=full_env, **kwargs)
