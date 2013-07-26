#!/bin/bash
# Commits from July 16-10

# Using github.com/mozilla-b2g/gaia.git and github.com/mozilla/mozilla-central
#    GITrepos/gaia@f207fcf201d463f183b7095a1f0464dae36ff31d..2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
#    GITrepos/gecko@2afa3fab9a667b6d5b5f894714bf960fdf85000f..584a1c3abf9e396f3a896244f57fbdd376dd6005


# Using github.com/mozilla-b2g/gaia.git and hg.mozilla.org/mozilla-central
#    GITrepos/gaia@f207fcf201d463f183b7095a1f0464dae36ff31d..2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
#    HGrepos/mozilla-central@94e902f5f517..b9a221ccef07

rm -f error.html bisect.html

bisect \
    -v \
    --script ./test.sh \
    GIT../repos/gaia@f207fcf201d463f183b7095a1f0464dae36ff31d..2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
    GIT../repos/gecko@2afa3fab9a667b6d5b5f894714bf960fdf85000f..584a1c3abf9e396f3a896244f57fbdd376dd6005

if [ -f error.html ] ; then
    open error.html
elif [ -f bisect.html ] ; then
    open bisect.html
fi

