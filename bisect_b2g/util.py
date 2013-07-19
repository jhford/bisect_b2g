#!/bin/false

import os
import subprocess
import logging

log = logging.getLogger(__name__)

devnull = open(os.devnull, 'w+')

def run_cmd(command, workdir=os.getcwd(), read_out=True, inc_err=False,
            ignore_err=True, env=None, delete_env=False, rc_only=False, **kwargs):
    """ Wrap subprocess in a way that I like.
    command: string or list of the command to run
    workdir: directory to do the work in
    inc_err: include stderr in the output string returned
    read_out: decide whether we're going to want output returned or printed
    env: add this dictionary to the default environment
    delete_env: delete these environment keys
    rc_only: run the command, ignore output"""

    full_env = dict(os.environ)

    if env:
        full_env.update(env)

    if delete_env:
        for d in delete_env:
            if full_env.has_key(d):
                del full_env[d]

    if inc_err and ignore_err:
        raise Exception("You are trying to include *and* ignore stderr, wtf?")
    elif inc_err:
        kwargs = kwargs.copy()
        kwargs['stderr'] = subprocess.STDOUT
    elif ignore_err:
        kwargs = kwargs.copy()
        kwargs['stderr'] = subprocess.PIPE # This might be a bad idea, research this!

    if rc_only:
        func = subprocess.call
        # This probably leaves a bunch of wasted open file handles.  Meh
        kwargs['stderr'] = kwargs['stdout'] = devnull
    elif read_out:
        func = subprocess.check_output
    else:
        func = subprocess.check_call

    log.debug("command=%s, workdir=%s, env=%s, kwargs=%s", command, workdir, env or {}, kwargs)
    return func(command, cwd=workdir, env=full_env, **kwargs)
