#!/usr/bin/env python

import sys
import os
import subprocess
import optparse
import tempfile
import logging
import math # Using math.log to determine how many iterations remain
import urlparse # Used to split apart URLs in parse_arg

import isodate # Used to parse dates from Git's broken ISO8601 output to tuples

log = logging.getLogger(__name__)

# Store global options.  Probably a bad idea
global_options = {}

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


class Repository(object):

    def __init__(self, name, url, local_path):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = local_path
        log.info("Setting up %s", name if name == local_path else "%s at %s" % (name, local_path))

    def sanitize(self):
        assert 0

    def update(self):
        assert 0

    def clone(self):
        assert 0

    def init_repo(self):
        assert 0

    def get_rev(self):
        assert 0

    def set_rev(self, rev):
        assert 0

    def validate_rev(self, rev):
        assert 0

    def rev_list(self, start, end):
        assert 0


class GitRepository(Repository):

    def __init__(self, *args):
        Repository.__init__(self, *args)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            log.debug("%s already exists, updating", self.name)
            self.update()
        else:
            log.debug("%s does not exist, cloning", self.name)
            self.clone()

    def clone(self):
        local_path_base = os.path.split(self.local_path)[0]

        if not os.path.exists(local_path_base) and local_path_base != '':
            os.makedirs(local_path_base)

        run_cmd(["git", "clone", self.url, self.local_path])

    def update(self):
        # Assuming here that all fetches go over the network
        pass#run_cmd(["git", "fetch", "--all"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["git", "rev-parse", "HEAD"], workdir=self.local_path)

    def set_rev(self, rev):
        # This will create a detached head
        run_cmd(["git", "reset", "--hard", "HEAD"], workdir=self.local_path)
        run_cmd(["git", "checkout", rev], workdir=self.local_path)
        log.debug("Set %s to %s", self.local_path, rev)

    def validate_rev(self, rev):
        pass

    def rev_list(self, start, end):

        def fix_git_timestamp(timestamp):
            """Yay git for generating non-ISO8601 datetime stamps.  Git generates, e.g.
            2013-01-29 16:06:52 -0800 but ISO8601 would be 2013-01-29T16:06:52-0800"""
            as_list = list(timestamp)
            as_list[10] = 'T'
            del as_list[19]
            return "".join(as_list)

        sep = " --- "
        command = ["git", "log"]

        if not global_options['follow_merges']:
            command.append("--first-parent")

        command.extend(["--date-order", "%s..%s" % (start, end),
                        '--pretty=%%H%s%%ci' % sep])
        raw_output = run_cmd(command, self.local_path )
        intermediate_output = [x.strip() for x in raw_output.split('\n')]
        output = []

        for line in [x for x in intermediate_output if x != '']:
            h,s,d = line.partition(sep)
            output.append((h, isodate.parse_datetime(fix_git_timestamp(d))))

        return output


class HgRepository(Repository):

    def __init__(self, *args):
        Repository.__init__(self, *args)
        if os.path.exists(self.local_path) and os.path.isdir(self.local_path):
            self.update()
        else:
            self.clone()

    def clone(self):
        run_cmd(["hg", "clone", self.url, self.local_path])

    def update(self):
        run_cmd(["hg", "pull", "-u"], workdir=self.local_path)

    def get_rev(self):
        return run_cmd(["hg", "identify"])

    def set_rev(self, rev):
        run_cmd(["hg", "update", "--rev", rev], workdir=self.local_path)

    def validate_rev(self, rev):
        assert 0

    def rev_list(self, start, end):
        assert 0


class Project(object):

    def __init__(self, name, url, local_path, good, bad, vcs="git"):
        object.__init__(self)
        self.name = name
        self.url = url
        self.local_path = local_path
        self.good = good
        self.bad = bad
        self.vcs = vcs

        if self.vcs == 'git':
            repocls = GitRepository
        elif self.vcs == 'hg':
            repocls = HgRepository
        else:
            log.error("Unsupported repository type")
            exit(1)
        
        log.debug("Using %s for %s", str(repocls), self.name)
        
        self.repository = repocls(self.name, self.url, self.local_path)

    def rev_list(self):
        if not hasattr(self, 'last_rl_id') or self.last_rl_id != (self.good, self.bad):
            self.last_rl_id = (self.good, self.bad)
            self.last_rl = self.repository.rev_list(self.good, self.bad)

        return self.last_rl

    def set_rev(self, rev):
        return self.repository.set_rev(rev)

    def __str__(self):
        return "Name: %(name)s, Url: %(url)s, Good: %(good)s, Bad: %(bad)s, VCS: %(vcs)s" % self.__dict__
    __repr__ = __str__


class Rev(object):

    def __init__(self, h, prj, date):
        object.__init__(self)
        self.h = h
        self.prj = prj
        self.date = date

    def __str__(self):
        return "%s@%s, %s" % (self.prj.name, self.h, self.date)
    __repr__=__str__


class N(object):

    def __init__(self, data, n):
        object.__init__(self)
        self.data = data
        self.n = n

    def __str__(self):
        return str(self.data)
    __repr__ = __str__


class InvalidArg(Exception): pass


def make_ll(l):
    """ Make a linked list such that l[0] is the first item is the list head returned"""
    rl = reversed(l[:])
    head = None

    for i in rl:
        head = N(i, head)

    return head


def build_history(projects):
    global_rev_list = []
    rev_lists = []
    last_revs = []
    for project in projects:
        rev_lists.append(make_ll([Rev(x[0], project, x[1]) for x in project.rev_list()]))

    def oldest(l):
        """Find the oldest head of a linked list and return it"""
        if len(l) == 1:
            log.debug("There was only one item to evaluate, returning %s", l[0].data)
            return l[0]
        else:
            oldest = l[0]
            for other in l[1:]:
                if other.data.date > oldest.data.date:
                    oldest = other
            log.debug("Found oldest: %s", oldest.data)
            return oldest

    def create_line(prev, new):
        log.debug("prev: %s", prev)
        log.debug("new:  %s", new)
        """ This function creates a line.  It will use the values in prev, joined with the value of new"""
        if len(new) == 1:
            # If we're done finding the oldest, we want to make a new line then
            # move the list of the oldest one forward
            global_rev_list.append([x.data for x in prev + new])
            rli = rev_lists.index(new[0])
            if rev_lists[rli].n == None:
                log.debug("Found the last revision for %s", rev_lists[rli].data.prj.name)
                last_revs.append(rev_lists[rli])
                del rev_lists[rli]
            else:
                log.debug("Moving pointer for %s forward", rev_lists[rli].data.prj.name)
                rev_lists[rli] = rev_lists[rli].n
            return
        else:
            # Otherwise, we want to recurse to finding the oldest objects
            o = oldest(new)
            if not o in prev:
                prev.append(o)
            del new[new.index(o)]
            log.debug("Building a line, %.2f%% complete ", float(len(prev)) / ( float(len(prev) + len(new))) * 100)
            create_line(prev, new)

    while len(rev_lists) > 0:
        create_line(last_revs[:], rev_lists[:])

    log.debug("Global History:")
    map(log.debug, global_rev_list)
    return global_rev_list


def _history_lines(line, prefix="  * "):
    return ["%s%s@%s" % (prefix, rev.prj.name, rev.h) for rev in line]


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


def _bisect(history, evaluator, max_recur, num):
    log.info('-' * 80)
    middle = len(history) / 2
    if len(history) == 1:
        log.debug("Found commit: %s", history[0])
        return history[0]
    else:
        cur = history[middle]
        log.info("Running test %d of %d or %d: ", num + 1, max_recur - 1, max_recur)
        map(log.info, _history_lines(cur))
        for rev in cur:
            log.debug("Setting revisions for %s", rev)
            rev.prj.set_rev(rev.h)
        outcome = evaluator(cur)

        if outcome:
            log.info("Test passed")
            return _bisect(history[middle:], evaluator, max_recur, num+1)
        else:
            log.info("Test failed")
            return _bisect(history[:middle], evaluator, max_recur, num+1)


# Make the first entry into the function a little tidier
def bisect(history, evaluator):
    max_recur = round(math.log(len(history) + len(history) % 2, 2))
    return _bisect(history, evaluator, max_recur, 0)


def local_path_to_name(lp):
    head, tail = os.path.split(lp)

    if tail.endswith('.git'):
        return tail[:4]
    else:
        return tail


def uri_to_name(uri):
    uri_bits = urlparse.urlsplit(uri)
    host = uri_bits.netloc
    host, x, path_base = host.partition(':')
    path_full = uri_bits.path

    if path_base != '':
        path_full = path_base + path_full

    name = path_full.split('/')[-1]

    if name.endswith('.git'):
        name = name[:4]

    return name


def parse_arg(arg):
    """
    Parse an argument into a dictionary with the keys:
        'uri' - This is a URI to point to a repository.  If it is a local file, no network cloning is done
        'good' - Good changeset
        'bad' - Bad changeset
        'local_path' - This is the path on the local disk relative to os.getcwd() that contains the repository

    The arguments that are parsed by this function are in the format:
        [GIT|HG][URI->]LOCAL_PATH@GOOD..BAD

    The seperators are '->', '..' and '@', quotes exclusive.  The URI and '->' are optional
    """
    arg_data = {}
    uri_sep = '@'
    rev_sep = '..'
    lp_sep = '->'

    if arg.startswith('HG'):
        vcs = 'hg'
        arg = arg[2:]
    elif arg.startswith('GIT'):
        vcs = 'git'
        arg = arg[3:]
    else:
        vcs = None # Careful, this gets used below because we want to
        # share the URI parsing logic, but we do the vcs token up here

    # Let's tease out the URI and revision range
    uri, x, rev_range = arg.partition(uri_sep)
    if x != uri_sep:
        raise InvalidArg("Argument '%s' is not properly formed" % arg)

    # Now let's get the good and bad changesets
    arg_data['good'], x, arg_data['bad'] = rev_range.partition(rev_sep)
    if x != rev_sep:
        raise InvalidArg("Argument '%s' is not properly formed" % arg)

    if os.path.exists(uri):
        local_path = uri
    else:
        # Non-local URIs need to determine the name and local_path
        if lp_sep in uri:
            uri, x, local_path = uri.partition(lp_sep)
            name = uri_to_name(uri)
        else:
            name = uri_to_name(uri)
            local_path = os.path.join(os.getcwd(), 'repos', name)

    # If the arg didn't start with a vcs token, we need to guess whether it's Git or HG
    if vcs == None:
        git_urls = ('github.com', 'codeaurora.org', 'linaro.org', 'git.mozilla.org')
        hg_urls = ('hg.mozilla.org')
        # Git can give itself away at times.  Yes, someone could have an hg repo that
        # ends with .git.  Wanna fight about it?
        if uri.startswith("git://") or uri.endswith(".git"):
            vcs = 'git'
        else:
            for hg_url in hg_urls:
                if hg_url in uri:
                    if vcs:
                        raise Exception("Multiple clues to VCS system")
                else:
                    vcs = 'hg'
            for git_url in git_urls:
                if git_url in uri:
                    if vcs:
                        raise Exception("Multiple clues to VCS system")
                else:
                    vcs = 'git'

    if vcs:
        arg_data['vcs'] = vcs
    else:
        raise Exception("Could not determine VCS system")

    arg_data['uri'] = uri
    arg_data['name'] = local_path_to_name(local_path)
    arg_data['local_path'] = local_path
    log.debug("Parsed '%s' to '%s'", arg, arg_data)
    return arg_data


def make_arg(arg_data):
    """ I am the reverse of parse_arg.  I am here in case someone else wants to
    generate these strings"""
    assert arg_data['uri'] == arg_data['local_path'], "unimplemented"
    return "%(local_path)s@%(good)s..%(bad)s" % arg_data


def main():
    parser = optparse.OptionParser("%prog - I bisect repositories!")
    parser.add_option("--script", "-x", help="Script to run.  Return code 0 \
                      means the current changesets are good, Return code 1 means \
                      that it's bad", dest="script")
    parser.add_option("--follow-merges", help="Should git/hg log functions \
                      follow both sides of a merge or only the mainline.\
                      This equates to --first-parent in git log",
                      dest="follow_merges", action="store_false")
    parser.add_option("-i", "--interactive", help="Interactively determine if the changeset is good",
                      dest="interactive", action="store_true")
    parser.add_option("-v", "--verbose", help="Logfile verbosity", action="store_true", dest="verbose")
    opts, args = parser.parse_args()

    file_handler = logging.FileHandler('bisection.log')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s/%(funcName)s:%(lineno)d - %(message)s"))
    log.addHandler(file_handler)
    
    if opts.verbose:
        file_handler.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)

    if opts.script and opts.interactive:
        log.error("You can't specify a script *and* interactive mode")
        parser.print_help()
        parser.exit(2)
    elif opts.script:
        evaluator = lambda x: script_evaluator(opts.script, x)
    else:
        evaluator = lambda x: interactive_evaluator(x)

    global_options['follow_merges'] = opts.follow_merges

    projects = []

    for arg in args:
        try:
            repo_data = parse_arg(arg)
        except InvalidArg as ia:
            log.error(ia)
            parser.print_help()
            parser.exit(2)

        projects.append(Project(
            name = repo_data['name'],
            url = repo_data['uri'],
            local_path = repo_data['local_path'],
            good = repo_data['good'],
            bad = repo_data['bad'],
            vcs = repo_data['vcs'],
        ))

    combined_history = build_history(projects)
    found = bisect(combined_history, evaluator)
    log.info("Found:")
    map(log.info, _history_lines(found))
    log.info("This was revision pair %d of %d total revision pairs" % \
    (combined_history.index(found) + 1, len(combined_history)))


if __name__ == "__main__":
    lh = logging.StreamHandler()
    log.addHandler(lh)
    lh.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)
    main()
