#!/bin/bash
clear
if [ "$1" == pdb ] ; then
    DBG="python -m pdb"
fi

#rm -rf repos


# July 16-10

$DBG ./bisect.py \
    --gaia-url git://github.com/mozilla-b2g/gaia.git \
    --gaia-branch master \
    --good-gaia f207fcf201d463f183b7095a1f0464dae36ff31d \
    --bad-gaia 2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
    --gaia-vcs git \
    --gecko-url git://github.com/mozilla-b2g/gonk-misc.git \
    --gecko-branch master \
    --good-gecko f0c701dad1c7352d567f4ddcf86c66ae2d5c8fda \
    --bad-gecko d4e6ca10162b4d3d79052b5b4721c4495640493e \
    --gecko-vcs git
