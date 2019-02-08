#!/usr/bin/env bash

cd $(dirname $(readlink -f $0))

find . -name *.pyc -exec rm -f {} \;
