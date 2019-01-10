#!/usr/bin/env bash

project_root=$(dirname $(readlink -f $0))

tag_name="$1"

echo ">>> prepare release <<<"
version_file="${project_root}/pgimp/__init__.py"
sed -i'' "s/__version__ = .*/__version__ = '$1'/" "${version_file}"
git commit -m "Prepare release $1." "${version_file}"
git push

echo ">>> create tag <<<"
git tag -am "v$1" "v$1"
git push origin "v$1"
