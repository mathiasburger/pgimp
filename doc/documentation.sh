#!/usr/bin/env bash
set -e

docdir=$(dirname $(readlink -f $0))
rootdir=$docdir/..

cd $rootdir/pgimp/doc/examples
files=`ls -1 *.py`

echo ">>> Generate documentation resources <<<"
cd $rootdir
for file in $files; do python3 -m pgimp.doc.examples.${file: : -3}; done

echo ">>> Build documentation <<<"
cd $docdir
rm -r build/
make html
