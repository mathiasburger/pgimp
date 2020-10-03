# Contributing

## Licensing and DCO

Source files must start with a license header including clarification on the copyright holders and an
spdx license identifier. Example:

```
# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT
```

By contributing to the project you agree with the [Developer Certificate of Origin](DCO.md).

### DCO Sign-Off Methods

The DCO requires a sign-off message in the following format appear on each commit in the pull request:

> Signed-off-by: Random J Developer <random@developer.example.org>

using your real name (sorry, no pseudonyms or anonymous contributions.)

The DCO text can either be manually added to your commit body, or you can add either **-s** or **--signoff** to
your usual git commit commands. If you forget to add the sign-off you can also amend a previous commit with the
sign-off by running **git commit --amend -s**. If you've pushed your changes to Github already you'll need to
force push your branch after this with **git push -f**.

## Project layout and style

A code file is always accompanied by a test file. For classes it will be named `*Test.py`, for modules
`*_Test.py`.

There must not be any todos in the code. Please open an issue or write an entry in [TODO.md](TODO.md).

## Testing

New functionality needs to be tested. The project is using pytest. Test environment configurations can be found
in `docker-compose.yml`. You may configure your IDE to use specific docker-compose services to run the tests.

### Build a specific container

```
docker-compose build <SERVICE_NAME>
```

### Troubleshooting a failed container build

Note the id of the last successful image that was build and start it with a shell to inspect the current state:

```
docker run --rm -it <CONTAINER_ID> /bin/bash
```

### Run tests in a specific container

Ubuntu
```
docker-compose run --rm pgimp-ubuntu-20.04 python3 -m pytest -c pytest.ini --maxfail=2 pgimp
```

CentOS
```
docker-compose run --rm pgimp-centos-7.4 scl enable rh-python36 'python3 -m pytest -c pytest.ini --maxfail=2 pgimp'
```

## Documentation

Classes and methods that make up the public API need to be documented. The sphinx documentation root is located
under `doc/`. Docstrings in python are used for documenting entities in the code. Each public method of the API
should also have a minimum working example.

## Quality checks

Execute the following to run quality checks (needs pylint which can be installed with e.g. `pip3 install pylint`:
```
./quality.sh
```

For detailed analysis [Gamma](https://mburger.os.mygamma.io) is used.

## Publishing

Is done by the maintainer using the following guidelines:
* [PyPI](https://python-packaging.readthedocs.io/en/latest/minimal.html)
* [Conda](https://conda.io/docs/user-guide/tutorials/build-pkgs.html)
* [Travis CI Publishing to PyPI](https://docs.travis-ci.com/user/deployment/pypi/)

Tags are created by the maintainer using `tag.sh`. They will be automatically published to the python packaging
index PyPI using the travis ci when the build of a tag passes.

Examples for tags (the script will prepend a `v` to the given name to indicate that it is a version tag):

```
./tag.sh 1.0.0-alpha-1
./tag.sh 1.0.0-beta-1
./tag.sh 1.0.0-rc-1
./tag.sh 1.0.0
```

Package and upload:
```
./packaging.sh
./packaging-upload.sh
```

## Verify that the package can be installed from pypi

Ubuntu
```
docker-compose build pgimp-ubuntu-20.04
docker-compose build pgimp-ubuntu-20.04-installation
```
