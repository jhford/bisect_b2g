#!/bin/bash
clear
if [ "$1" == pdb ] ; then
    DBG="python -m pdb"
fi

#rm -rf repos


# July 16-10

cmd="$DBG ./bisect.py \
    --script ./test.sh \
    --gaia-url git://github.com/mozilla-b2g/gaia.git \
    --gaia-branch master \
    --good-gaia f207fcf201d463f183b7095a1f0464dae36ff31d \
    --bad-gaia 2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
    --gaia-vcs git \
    --gecko-url git://github.com/mozilla-b2g/gonk-misc.git \
    --gecko-branch master \
    --good-gecko 2afa3fab9a667b6d5b5f894714bf960fdf85000f \
    --bad-gecko 584a1c3abf9e396f3a896244f57fbdd376dd6005 \
    --follow-merges \
    --gecko-vcs git"
echo $cmd
$cmd
