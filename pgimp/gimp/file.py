from typing import Callable

import gimp
from gimp import Image
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


def for_each_file(callback):
    # type: (Callable[[Image, str], None]) -> None
    files = get_json('__files__')
    for file in files:
        image = open_xcf(file)
        callback(image, file)
        gimp.pdb.gimp_image_delete(image)
