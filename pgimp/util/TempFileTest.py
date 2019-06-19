# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os

from pgimp.util.TempFile import TempFile, use_shmem, shmem_dir


def test_tempfile_is_removed():
    with TempFile() as f:
        assert 'tmp' in f
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


def test_memory_gets_freed_in_shm():
    if use_shmem():
        with TempFile() as f:
            fh = open(f, 'w')
            fh.write('x' * (100 * 1000000))  # write 100M
            fh.close()
            statvfs = os.statvfs(shmem_dir())
            free_before = statvfs.f_frsize * statvfs.f_bavail / 1000000  # disk free in M
        statvfs = os.statvfs(shmem_dir())
        free_after = statvfs.f_frsize * statvfs.f_bavail / 1000000  # disk free in M
        assert free_after > free_before + 100*0.8  # at least 80 M more space than before
