#!/usr/bin/env bash

cd $(dirname $(readlink -f $0))

echo ">>> cleaning up <<<"
rm -r pgimp.egg-info/
rm -r dist/
rm -r gimp/
rm -r gimpenums/
rm -r gimpfu/

echo ">>> creating distribution files <<<"
# do not create bdist_wheel because of content that needs to be generated on the target system
# gimp's documentation was not created by this project and thus cannot be packaged
python3 setup.py sdist
