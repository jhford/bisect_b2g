#!/bin/bash

rm -f bisection.log error.html bisect.html

# HGhttp://hg.mozilla.org/integration/gaia-central-\>../repos/gaia-hg@good..bad \
# Dates July 23, 2013 -> July 31, 2013
bisect \
    -v \
    --profile-output profile.data \
    --script ./test.sh \
    GIThttps://github.com/mozilla-b2g/gaia.git-\>gaia@4705192..7577eb7 \
    HGhttps://hg.mozilla.org/mozilla-central-\>mozilla-central@34a46f10c5a0d80bb17c0039bfcb834ed75ffbff..97b2b5990840199b347d3f21bd7e6543d2bdf155

if [ -f error.html ] ; then
    open error.html
elif [ -f bisect.html ] ; then
    open bisect.html
fi

