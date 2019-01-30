# pgimp

[![Build Status](https://travis-ci.org/mabu-github/pgimp.svg?branch=master)](https://travis-ci.org/mabu-github/pgimp)
[![Docs](https://readthedocs.org/projects/pgimp/badge/?version=latest&style=flat)](https://readthedocs.org/projects/pgimp/)

Interacting with gimp in python3.

Use Cases:
* Autocompletion for writing gimp scripts.
* Batch creation or update of gimp files or data extraction from gimp files.
* Workflows where machine learning data has to be annotated. Raw data 
  can be converted to gimp files where the annotation process can happen (gimp's thresholding tools 
  etc. make it easy to do annotation for pixelwise segmentation). After the masks are created, they 
  can be converted back to e.g. numpy files.

Read the [documentation](https://pgimp.readthedocs.io/en/latest/) for details on what pgimp can 
do for you and how it is achieved. Every single public method comes with a short working example!

## Skeletons for autocompleting gimp scripts

On setup, the `GimpDocumentationGenerator` will generate python skeletons for the methods that gimp 
exposes to the interpreter through the procedural database (pdb). This enables autocompletion in your IDE.

## Run a python script within gimp

Running python code within gimp is performed by the `GimpScriptRunner`. Have a look at the corresponding test 
`GimpScriptRunnerTest` to see how this works.

You may import convenience functions from `pgimp.gimp` in your gimp python scripts. 
See `pgimp.GimpScriptRunnerTest.test_import_from_pgimp_library`.

# Installation

The package manager `pip` and the python packages `setuptools` and `psutil` are required in order 
to install the package. As gimp uses a python2 interpreter, 
the pip packages `numpy` and `typing` for python2 need to be installed.

## Operating system dependent infos

### Linux

On Linux, install the gimp package, e.g. `sudo apt-get install gimp` for Debian/Ubuntu. In order to run headless, 
install xfvb, e.g. `sudo apt-get install xvfb`.

### Mac OS

Install gimp from gimp.org or via homebrew.

### Windows

Windows is not supported.

## Using pip

```
pip3 install pgimp
```

## Using conda

Using a conda environment.yml file:
```
name: <NAME_OF_THE_ENV>
channels:
  - defaults
dependencies:
  - python=<3.6+>
  - pip:
    - pgimp
```

## From github

Using pip:
```
pip3 install git+https://github.com/mabu-github/pgimp
```

Using a conda environment.yml file:
```
name: <NAME_OF_THE_ENV>
channels:
  - defaults
dependencies:
  - python=<3.6+>
  - pip:
    - "git+https://github.com/mabu-github/pgimp"
```

## Local

Install using symlink to checked out code (for development):
```
pip3 install -e .
```

# Contributing and Publishing

See [CONTRIBUTING.md](CONTRIBUTING.md).

# License
 This project is licensed under the MIT license. See the [LICENSE](LICENSE) file for more info.
