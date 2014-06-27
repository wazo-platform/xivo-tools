#!/bin/bash

#apt-get install git build-essential python-dev debhelper

PKGNAME="$1"
BRANCH="master"
GIT_ROOT="git://git.xivo.io/official"

[ -n "$2" ] && BRANCH="$2"

function clone_or_pull_repo() {
    repo="$1"
    if [ ! -d "$repo" ]; then
        git clone $GIT_ROOT/$repo.git
    else
        cd $repo
        git fetch -p
        cd ..
    fi
}

function buildpkg() {
    pkgname="$1"
    branch="$2"
    cp -r squeeze-xivo-skaro/$pkgname/trunk/debian $pkgname/$pkgname
    cd $pkgname/$pkgname
    git checkout $branch
    git reset --hard origin/$branch
    dpkg-buildpackage -tc
    cd ../..
}

clone_or_pull_repo squeeze-xivo-skaro
clone_or_pull_repo $PKGNAME
buildpkg $PKGNAME $BRANCH
mv $PKGNAME/*.deb .
