Welcome to pgimp's documentation!
=================================

Pgimp let's you interact with gimp in python3. Gimp itself only allows you
to use python2 and the documentation of its procedural database (pdb) is C-style
and not integrated into your IDE.

Therefore pgimp generates python skeletons
for full autocompletion and documentation when writing scripts that will be
executed within gimp's python interpreter.

Furthermore pgimp provides python3 classes and methods to interact with gimp files
or whole collections of files conveniently.

Use cases
=========

* Autocompletion for writing gimp scripts.
* Batch creation or update of gimp files or data extraction from gimp files.
* Workflows where machine learning data has to be annotated. Raw data
  can be converted to gimp files where the annotation process can happen (gimp's thresholding tools
  etc. make it easy to do annotation for pixelwise segmentation). After the masks are created, they
  can be converted back to e.g. numpy files.

Table of content
================

.. toctree::
   :maxdepth: 3

    Tutorial <tutorial.rst>
    API Documentation <apidoc.rst>

Indices and tables
==================

* :ref:`genindex`
