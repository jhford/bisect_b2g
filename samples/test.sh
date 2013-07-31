#!/bin/bash

# From git gaia 5a1c8dd69f66c8b5a7f2e5bc0fc183992af07b44's second parent

grep '           <span id="dialer-message-text" data-l10n-id="NoPreviousOutgoingCalls" hidden> </span>'\
    gaia/apps/communications/dialer/index.html

if [ $? -eq 0 ] ; then
    echo FOUND
    exit 0
else
    echo NOTFOUND
    exit 1
fi
