Copyright check
===============

A git hook to fix copyright dates in code files.

To use this hook create a link in your .git/hook directory named pre-commit

To install in all your git repos:

    cd <root/of/your/projects>
    find -path '*/.git/hooks' -exec ln  <path/to/copyright-check>/copyright-check {}/pre-commit \;


Changelog check
===============

A git hook to avoid committing without updating the debian/changelog.

To use this hook create a link in your .git/hook directory named pre-commit
