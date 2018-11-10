# pgimp

Call gimp routines from python3 code.

## Create skeletons for gimp python autocompletion

When writing scripts to be executed within gimp, it is useful to have IDE autocompletion. `GimpDocumentationGenerator` 
can generate python skeletons for this task. The corresponding test `GimpDocumentationGeneratorTest` describes how 
to write the skeleton.

## Run a python script within gimp

Running python code within gimp is performed by the `GimpScriptRunner`. Have a look at the corresponding test 
`GimpScriptRunnerTest` to see how this works.

## Convenience function library

You may import convenience functions from `pgimp.gimp` in your gimp python scripts. 
See `pgimp.GimpScriptRunnerTest.test_import_from_pgimp_library`.

# Installation

## Operating system dependent infos

### Linux

On Linux, install the gimp package, e.g. `sudo apt-get install gimp` for Debian/Ubuntu. 

### Mac OS

Install gimp from gimp.org or via homebrew.
```

### Windows

Windows is not supported.

## From github

```
pip3 install git+https://github.com/mabu-github/pgimp
```

## Local

Install using symlink to checked out code (for development):
```
pip3 install -e .
```

# Publishing

Follow the guidelines for:
* [PyPI](https://python-packaging.readthedocs.io/en/latest/minimal.html)
* [Conda](https://conda.io/docs/user-guide/tutorials/build-pkgs.html)

