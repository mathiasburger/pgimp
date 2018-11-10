#!/usr/bin/env bash

cdir=$(dirname $(readlink -f $0))

cd $cdir
rm -r build/
make html
