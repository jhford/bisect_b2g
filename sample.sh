#!/bin/bash
clear

./bisect.py \
    --gaia-url git://github.com/mozilla-b2g/device-leo.git \
    --gaia-branch master \
    --good-gaia 837cb4d449281b3990bbdb4c34e3f86c52d83ab3 \
    --bad-gaia 7d0fbcb1ea75de5edc0bf5750752d5cf2d226b93 \
    --gaia-vcs git \
    --gecko-url git://github.com/mozilla-b2g/device-inari.git \
    --gecko-branch master \
    --good-gecko 97858bf095e37b78132f0f98a0e1120e95a88ab1 \
    --bad-gecko 71324335d7fcb44e1f81e0c47499d47d2a44bfed \
    --gecko-vcs git
