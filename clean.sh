#!/usr/bin/env bash

cd $(dirname $(readlink -f $0))

find . -type d -name __pycache__ -exec rm -rf {} \;
