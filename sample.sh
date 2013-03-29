#!/bin/bash
clear

./bisect.py \
    --gaia-url git://github.com/mozilla-b2g/gaia.git \
    --gaia-branch master \
    --good-gaia lalagood \
    --bad-gaia lalabad \
    --gaia-vcs git \
    --gecko-url http://hg.mozilla.org/mozilla-central \
    --gecko-branch master \
    --good-gecko lalagood \
    --bad-gecko lalabad \
    --gecko-vcs hg
