# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os

from pgimp.util.TempFile import TempFile


def test_file_not_created():
    with TempFile() as f:
        assert 'tmp' in f
        assert not os.path.exists(f)

    assert not os.path.exists(f)


def test_tempfile_is_removed():
    with TempFile() as f:
        assert 'tmp' in f
        open(f, 'w').close()
        assert os.path.exists(f)

    assert not os.path.exists(f)


def test_tempfile_is_removed_on_exception():
    try:
        with TempFile() as f:
            assert 'tmp' in f
            open(f, 'w').close()
            assert os.path.exists(f)
            raise ValueError
    except ValueError:
        pass

    assert not os.path.exists(f)
