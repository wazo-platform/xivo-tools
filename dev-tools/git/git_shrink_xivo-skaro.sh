#!/usr/bin/env bash

# Strips a repo history from files or directories

# Run it inside the repository to shrink. You must then clone this repo into
# another and prune the new repo.

# You can cancel the modifications with "git reset --hard HEAD@{1}".

REPO=xivo-skaro
BIG_FILES="\
asterisk/tarballs \
asterisk-sounds-* \
chan_sccp/tarballs \
dahdi-linux/tarballs \
dahdi-tools/tarballs \
freeswitch wanpipe/tarballs \
openssl-0.9.8g-mingw \
phones-firmware \
prompts \
web-interface/datastorage/sqlite/xivo.db \
xivo-sounds \
"

git filter-branch \
-d /dev/shm/git/$REPO \
--prune-empty \
--index-filter "git rm -rf --cached --ignore-unmatch $BIG_FILES" \
--tag-name-filter cat -- \
--all
