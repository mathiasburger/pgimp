# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import tempfile


class TempFile:
    def __init__(self, suffix='', prefix=tempfile.template) -> None:
        super().__init__()
        self._file = None
        self._suffix = suffix
        self._prefix = prefix

    def __enter__(self):
        self._file = tempfile.mktemp(suffix=self._suffix, prefix=self._prefix)
        return self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self._file):
            os.remove(self._file)
        return False
