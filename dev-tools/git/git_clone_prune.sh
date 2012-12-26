#!/usr/bin/env bash

# Clone a repo and prune it of unused object files (use it after a git filter-branch)

git clone $1 $2

cd $2

git gc --prune=now
