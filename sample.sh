#!/bin/bash
clear
if [ "$1" == pdb ] ; then
    DBG="python -m pdb"
fi

#rm -rf repos


# July 16-10
#    GITrepos/gaia@f207fcf201d463f183b7095a1f0464dae36ff31d..2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
#    GITrepos/gecko@2afa3fab9a667b6d5b5f894714bf960fdf85000f..584a1c3abf9e396f3a896244f57fbdd376dd6005 \

cmd="$DBG ./bisection.py \
    --script ./test.sh \
    GITrepos/gaia@f207fcf201d463f183b7095a1f0464dae36ff31d..2cff2fbbf3c70f410a50c59c141333052e7ae2b3 \
    GITrepos/gecko@2afa3fab9a667b6d5b5f894714bf960fdf85000f..584a1c3abf9e396f3a896244f57fbdd376dd6005 \
"
echo $cmd
$cmd
