# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Callable

import gimp

from pgimp.gimp.parameter import get_json


def open_xcf(filename):
    """
    :type filename: str
    :rtype: gimp.Image
    """
    return gimp.pdb.gimp_xcf_load(0, filename, filename)


def save_xcf(image, filename):
    """
    :type image: gimp.Image
    :type filename: str
    """
    gimp.pdb.gimp_xcf_save(0, image, None, filename, filename)


def close_image(image):
    """
    :type image: gimp.Image
    :return:
    """
    gimp.pdb.gimp_image_delete(image)


class XcfFile:
    def __init__(self, file, save=False):
        """
        :type file: str
        :type save: bool
        """
        self._file = file
        self._save = save
        self._image = None

    def __enter__(self):
        """
        :rtype: gimp.Image
        """
        self._image = open_xcf(self._file)
        return self._image

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._save:
            save_xcf(self._image, self._file)
        close_image(self._image)
        return False


def for_each_file(callback, save=False):
    # type: (Callable[[gimp.Image, str], None], bool) -> None
    files = get_json('__files__')
    for file in files:
        with XcfFile(file, save=save) as image:
            callback(image, file)
