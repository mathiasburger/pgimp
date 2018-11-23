# Contributing

## Project layout and style

A code file is always accompanied by a test file. For classes it will be named *Test.py, for modules *_Test.py.

There must not be any todos in the code. Please open an issue or write an entry in [TODO.md](TODO.md).

## Testing

New functionality needs to be tested. The project is using pytest. Test environment configurations can be found 
in `docker-compose.yml`. You may configure your IDE to use specific docker-compose services to run the tests.

## Documentation

Classes and methods that make up the public API need to be documented. The sphinx documentation root is located 
under `doc/`. Docstrings in python are used for documenting entities in the code. Each public method of the API 
should also have a minimum working example.

## Publishing

Is done by the maintainer using the following guidelines:
* [PyPI](https://python-packaging.readthedocs.io/en/latest/minimal.html)
* [Conda](https://conda.io/docs/user-guide/tutorials/build-pkgs.html)
* [Travis CI Publishing to PyPI](https://docs.travis-ci.com/user/deployment/pypi/)
