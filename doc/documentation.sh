#!/usr/bin/env bash

cdir=$(dirname $(readlink -f $0))

cd $cdir
sphinx-apidoc -o source/ ../pgimp
make html
