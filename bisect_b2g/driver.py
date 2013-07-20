import os
import optparse
import urlparse
import logging

log = logging.getLogger(__name__)

import bisect_b2g
from bisect_b2g.repository import Project
from bisect_b2g.bisection import Bisection
from bisect_b2g.history import build_history
from bisect_b2g.evaluator import script_evaluator, interactive_evaluator


class InvalidArg(Exception): pass


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

    # Set up logging
    bisect_b2g_log = logging.getLogger(bisect_b2g.__name__)
    bisect_b2g_log.setLevel(logging.DEBUG)
    lh = logging.StreamHandler()
    lh.setLevel(logging.INFO)
    bisect_b2g_log.addHandler(lh)
    file_handler = logging.FileHandler('bisection.log')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s/%(funcName)s:%(lineno)d - %(message)s"))
    bisect_b2g_log.addHandler(file_handler)
    
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

    projects = []

    if len(args) < 2:
        log.error("You must specify at least two repositories")
        parser.print_help()
        parser.exit()

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
            follow_merges = opts.follow_merges,
        ))

    combined_history = build_history(projects)
    bisection = Bisection(projects, combined_history, evaluator)
    bisection.write('history.html')
    bisection.write('history.xml', fmt='xml')
    log.info("Found:")
    map(log.info, ["  * %s@%s" % (rev.prj.name, rev.hash) for rev in bisection.found])
    log.info("This was revision pair %d of %d total revision pairs" % \
    (combined_history.index(bisection.found) + 1, len(combined_history)))


if __name__ == "__main__":
    main()
