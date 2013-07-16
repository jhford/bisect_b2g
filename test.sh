#!/bin/bash

cd repos/gecko

# From 8d8af3f039d5f3bdf24b91cd0ce62798e1feac96
grep '<form role="dialog" data-type="confirm">' /home/jhford/bisect-b2g/repos/gaia/apps/camera/index.html

if [ $? -eq 0 ] ; then
    echo FOUND
    exit 0
else
    echo NOTFOUND
    exit 1
fi
