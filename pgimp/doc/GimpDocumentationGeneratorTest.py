# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os

from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file


def test_generate_python_skeletons():
    generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
        file.relative_to(__file__, '../../gimp')
    ))
    generate_python_skeleton()

    def assert_file_exists(f: str):
        assert os.path.exists(os.path.join(file.relative_to(__file__, '../../'), f))

    assert_file_exists('gimp/__init__.py')
    assert_file_exists('gimp/pdb.py')
    assert_file_exists('gimpenums/__init__.py')
    assert_file_exists('gimpfu/__init__.py')
