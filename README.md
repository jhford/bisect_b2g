## Bisect All The Repositories
[![Build
Status](https://travis-ci.org/jhford/bisect_b2g.png)](https://travis-ci.org/jhford/bisect_b2g)

## Installation
Simple case, using a possibly old version on PyPi:

    pip install bisect-b2g

If you want to hack on `bisect_b2g`:

    git clone https://github.com/mozilla-b2g/bisect_b2g
    cd bisect_b2g
    virtualenv --version || pip install virtualenv
    virtualenv .
    source bin/activate
    python setup.py develop

If you want to run the tests

    cd bisect_b2g
    source bin/activate
    make check

## Background

`bisect_b2g` wants to tell you which set of revisions broke you.

`bisect_b2g` works across different repositories.  It currently supports Git
and Mercurial based repositories.  The program can use either a script or
interactive session to evaluate bisection across two or more repositories.  One
day `bisect --help` may even provide useful information!

It's important to have some level of understanding of how this program works.
Normal bisecting within a single repository can be done using structural
information stored in the revision graph.  Once you start crossing between
repositories you need to figure out a way to interleave their history.
`bisect_b2g` currently uses the commit timestamp for the commits in the
specified commit range to interleave the repositories together.  This is
somewhat tricky because it requires that the committer have had a correct clock
when the commit was made.

Given two repositories `A` and `B` that have commits made in the order `A1`,
`B2`, `A3`, `B4`, `A5`, `B6`:

    A1
     |   B2
    A3   |
     |   B4
    A5   |
         B6

`bisect_b2g` will try to convert the two unrelated histories into a single coherent history:

    A1 + B2
       |
    A3 + B2
       |
    A3 + B4
       |
    A5 + B4
       |
    A5 + B6

At this point a bisection is commenced using this single history beginning at
the known good revision set and ending at the known bad revision set.  The
midpoint of the list is tested and if it matches the criteria that makes a
commit set 'good', `bisect_b2g` is able to assert that this new 'good'.  When
`bisect_b2g` has determined that a tested revision set is either 'good' or
'bad', it changes the original 'good' or 'bad' points and tests the new
midpoint of that range.  Once `bisect_b2g` has only a single item in the
new revision set range, We've found both the last good and the first bad
revision set and present our findings

## Usage
To use `bisect_b2g`, you have to start somewhere else.  You need the following information:

* What repositories are involved
* The latest commit in each repository that was good
* The earliest commit in each repository that was bad
* The URL of each repository, or a path to a clone on your system
* How you can test a revision set.  Programmaticaly with a script is ideal

Let's create our `bisect_b2g` command line.  We'll start with the revision set specifiers.

### Describing a repository and revision range
The repository and revision ranges are communicated to `bisect_b2g` through command line arguments.  Valid forms are:

* `local_path@good..bad` -- take the repository at path `local_path` as is.
  Mark `good` as the last known good commit and `bad` as the first known bad
  commit.  This is similar to a Mercurial revset (`good:bad`) or Git commit
  ranges (`good^..bad`)
* `repositoryurl->local_path@good..bad` -- Take the repository at
  `repositoryurl` and clone it to `local_path.  Remainder handled as above

`bisect_b2g` needs to know if a given repository is Mercurial or Git.  It knows
that certain url patterns are indicative of Git and others of Mercurial.  It
knows that certain hostnames are Git and others are Mercurial.  This detection
is rather weak, so a better idea is to use the VCS prefixes.

* `HG` prefix instructs `bisect_b2g` to use Mercurial, example:
  `HGhttp://hg.mozilla.org/mozilla-central`
* `GIT` prefix instructs `bisect_b2g` to use Git, example:
  `GIThttps://github.com/mozilla-b2g/gaia.git`

`bisect_b2g` can be invoked using the `bisect` command.  There are currently
two ways to evaluate a revision set: interactive and script.

### Evaluators
Evaluators are what `bisect_b2g` uses to descide whether a give revision set is
good or bad.  The revisions for the repositories are set properly by
`bisect_b2g`, so there's no need for the Evaluator to do any vcs operations.
There are two built in `Evaluators`: `ScriptEvaluator` and
`InteractiveEvaluator

The `ScriptEvaluator` is requested by using the `--script path/to/script`
option of `bisect`.  The argument passed must be an executable script which
will evaluate a revision set to be good by exiting with an exit code of `0` or
bad by exiting with any other status.  The script is run from the same
directory as the `bisect` program, so relative paths are based on the same
working directory as those used in the repository and revision range
specifications.

The `InteractiveEvaluator` is requested by using the `-i` option to `bisect`.
When `bisect_b2g` needs to evaluate a revision set it will start a bash session
with two commands defined: `good` and `bad`.  You can do whatever you need to
evaluate the revision set.  Once you've determined the state of, run either
`good` or `bad` to mark the revision set and move on.

### Example 1: ScriptEvaluator with Mozilla Central and Gaia
This example is more to demonstrate how to use the program than make a
compelling argument for `bisect_b2g` In this example, we are trying to figure
out what version of Mozilla-Central was current when the `<span
id="dialer-message-text" data-l10n-id="NoPreviousOutgoingCalls" hidden>
</span>` showed up.  We had a good idea that it wasn't there when Gaia was at
`4705192` but was there by `7577eb7`.  We know that a roughly corresponding
Mozilla Central revision range was `34a46f10c5a0` to `97b2b5990840`.  We also
know where the repositories are located on the network.

We create a file in the current working directory called `test.sh`

    grep '           <span id="dialer-message-text" data-l10n-id="NoPreviousOutgoingCalls" hidden> </span>' \
    gaia/apps/communications/dialer/index.html
    
    if [ $? -eq 0 ] ; then
        echo FOUND
        exit 0
    else
        echo NOTFOUND
        exit 1
    fi

Next, we run `bisect`

    bisect -v --script ./test.sh \
        GIThttps://github.com/mozilla-b2g/gaia.git-\>gaia@4705192..7577eb7 \
        HGhttps://hg.mozilla.org/mozilla-central-\>mozilla-central@34a46f10c5a0..97b2b5990840

Then watch the output:

    Setting up https://github.com/mozilla-b2g/gaia.git->gaia
    Setting up https://hg.mozilla.org/mozilla-central->mozilla-central
    Running test 1 of 7
    gaia@b1ea7ffb32ecd0ab9ff6b263c4363c314e0909a5
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test pass
    Running test 2 of 7
    gaia@edb1dea8b45238add44b199cf02c9b4ed808b767
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test fail
    Running test 3 of 7
    gaia@c7272f0b45c9fdac9d551828987e343300e87bf6
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test pass
    Running test 4 of 7
    gaia@faf51f36abcec0a349ff44ab7a7de10fe0010314
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test fail
    Running test 5 of 7
    gaia@80f8e8f733c837ab5c3bd1cccae82df9000446da
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test fail
    Running test 6 of 7
    gaia@466f7aeabcaf1fc85f6b33a215d485e83b5a925c
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test fail
    Running test 7 of 7
    gaia@5a1c8dd69f66c8b5a7f2e5bc0fc183992af07b44
    mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    Test pass
    Found:
      * gaia@5a1c8dd69f66c8b5a7f2e5bc0fc183992af07b44
      * mozilla-central@eb89f19070ae9b03bac5c7e1c0f7c26e4e058817
    This was revision pair 79 of 124 total revision pairs

The first changeset contains our `<span>`, was `5a1c8dd69f66c8b5a7f2e5bc0fc183992af07b44`

### Example 2: InteractiveEvaluator with contrived repository

Here's a script that'll start an interactive session.  It's in a script to
simplify repository generation

    base_repo_dir=test_repos

    function create_simple_interleave () {
        repos=$1 ; shift
        commits=$1 ; shift

        seconds=0

        for r in $repos ; do
            repodir="$base_repo_dir/$r"
            rm -rf "$repodir"
            mkdir -p "$repodir"
            (cd "$repodir" && git init)
        done

        for c in $commits ; do
            for r in $repos ; do
                repodir="$base_repo_dir/$r"
                commit_data="$r-$c"
                git_time=$(python -c "print \"2%03d-01-01T00:00:00-0300\" % $seconds")
                seconds=$((seconds + 1))
                (cd $repodir &&
                    echo "$r-$c" > $r &&
                    git add $r &&
                    GIT_COMMITTER_DATE=$git_time \
                    GIT_AUTHOR_DATE=$git_time \
                        git commit -a -m "$commit_data" &&
                    git tag "$commit_data"
                )
            done
        done
    }

    function get_rev () {
       repo=$1 ; shift
        commit=$1 ; shift
        (cd "$base_repo_dir/$repo" && git rev-parse "$commit")
    }

    create_simple_interleave "A B C D" "1 2 3 4 5 6 7 8 9"

    bisect -i -v \
        "GIT$base_repo_dir/A@$(get_rev A A-1)..$(get_rev A A-9)" \
        "GIT$base_repo_dir/B@$(get_rev B B-1)..$(get_rev B B-9)" \
        "GIT$base_repo_dir/C@$(get_rev C C-1)..$(get_rev C C-9)" \
        "GIT$base_repo_dir/D@$(get_rev D D-1)..$(get_rev D D-9)" \

If you use the order `good good good good good good`, you'll get the result

    Found:
      * A@b868b1fbb5c38ba945cc96a70bdf150a84ae6a90
      * B@f2a0af82789a2df8712e7fcb6fdd7be5f4e62eb1
      * C@e4ed7b27a2de31a2762e65915c649c38d64aefa1
      * D@d88244d6983c5c026910d679a8567e4299a73008
    This was revision pair 36 of 36 total revision pairs

Which is the same set of commits that are 'good'

###bisect.html
In case you are a visual person, I generate a nifty chunk of self-contained
HTML that presents the outcome and results in a table that's filterable and can
optionally show you tags instead of commits

## Bugs and Future Improvement
Even though I do have tests, I don't have every possibility covered.  Right now
the biggest issues are:

* Implementing a replacement for `--first-parent` in mercurial
* I am sure that the history simplification isn't perfect
* There are no tests for the history interleaving routines.  Eeek!
* My mako html templates are currently in a python string instead of a file.
  Booo!
* My mako html template is very slow
* lolwindows

I would like to use the gaia.json file to create an alternate history builder
and interleaver that's able to better deal with Gecko and Gaia pairings.  This
would give us a significantly more solid idea of what was going on on those
repositories.  Even better would be a general service which as a post commit
hook to all of our repositories stored the commits on that repository so that
we could build something to tell us the state of all the other repositories
when a given changeset was the tip.

Instead of using git and hg log functions, I'd like to walk the DAG myself.

## Contributions
They're welcome.  I am trying to figure out travis integration, but once that's
going, passing tests on travis will be a requirement of landing in the
repository.  Pull requests are welcomed!  If you have an sample of where
`bisect_b2g` was helpful in solving a problem for you, a reproducible script of
the bisection for the samples and tests is greatly appreciated


## LICENSE

Copyright (c) 2013 Mozilla Foundation

Contributors: John Ford <jhford.mozilla@com>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
