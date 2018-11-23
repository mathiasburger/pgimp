#!/usr/bin/env bash

tag_name="$1"
git tag -am "v$1" "v$1"
git push origin "v$1"
