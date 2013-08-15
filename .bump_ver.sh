#!/bin/bash
cur_ver=$(sed < setup.py '/version/!d ; s/^.*version *= *"//g ; s/".*$//g')
new_ver=$(( cur_ver + 1 ))
echo $new_ver
