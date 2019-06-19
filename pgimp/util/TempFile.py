# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import tempfile

USE_SHMEM = None
SHMEM_DIR = '/dev/shm'


def use_shmem():
    global USE_SHMEM, SHMEM_DIR
    if USE_SHMEM is None:
        USE_SHMEM = os.path.exists(SHMEM_DIR)
    return USE_SHMEM


def shmem_dir():
    global SHMEM_DIR
    if use_shmem():
        return SHMEM_DIR
    return None


class TempFile:
    def __init__(self, suffix='', prefix=tempfile.template) -> None:
        super().__init__()
        self._file = None
        self._suffix = suffix
        self._prefix = prefix

    def __enter__(self):
        self._file = tempfile.mkstemp(suffix=self._suffix, prefix=self._prefix, dir=shmem_dir())[1]
        return self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self._file):
            os.remove(self._file)
        return False
