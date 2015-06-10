xivo-fai-deploy
===============

This is the description of a Jenkins job named xivo-fai-deploy. It has become
obsolete with the arrival of the xivo-dist script.

Jenkins job
-----------

To be run on builder@builder-wheezy:

```
cd /home/builder/packages/xivo-fai

rm -vf ../xivo-fai-*
rm -vf ../xivo-fai_*

git pull
echo $(xivo-version unstable) >>xivo-versions

export DEBFULLNAME="XiVO Builder Team"
export DEBEMAIL="release@xivo.io"
bash -x xivo-fai-build

git add data debian/control debian/changelog xivo-versions
git commit -m "build fai for xivo $(xivo-version unstable)"
git push
```

To be run on root@mirror.xivo.io:

```
reprepro -vb /data/reprepro/xivo processincoming xivo-dev
reprepro -vb /data/reprepro/xivo processincoming xivo-rc
reprepro -vb /data/reprepro/xivo processincoming xivo-five
reprepro -vb /data/reprepro/xivo processincoming squeeze
reprepro -vb /data/reprepro/xivo processincoming squeeze-dev
```

Notes
-----

The script ``xivo-fai-build`` is available in the
git.xivo.fr:official/xivo-fai.git repo.
