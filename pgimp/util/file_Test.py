# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import tempfile

from pgimp.util.file import copy_relative, relative_to


def test_copy_with_filename_only():
    src = relative_to(__file__, 'test-resources/a/file')

    copy_relative(src, 'file_copy')

    expected = relative_to(__file__, 'test-resources/a/file_copy')
    assert os.path.exists(expected)

    os.remove(expected)


def test_copy_with_relative_path():
    src = relative_to(__file__, 'test-resources/a/file')

    copy_relative(src, '../b/file_copy')

    expected = relative_to(__file__, 'test-resources/b/file_copy')
    assert os.path.exists(expected)

    os.remove(expected)


def test_copy_with_absolute_path():
    src = relative_to(__file__, 'test-resources/a/file')
    tmp = tempfile.mktemp()

    copy_relative(src, tmp)

    expected = tmp
    assert os.path.exists(expected)

    os.remove(expected)
