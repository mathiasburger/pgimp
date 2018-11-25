# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import gimp

from pgimp.gimp.file import open_xcf


def create_from_template_image(template):
    """
    :type template: gimp.Image
    :rtype: gimp.Image
    """
    width = template.width
    height = template.height
    type = template.base_type
    image = gimp.pdb.gimp_image_new(width, height, type)
    return image


def create_from_template_file(template_file):
    """
    :type template: str
    :rtype: gimp.Image
    """
    template = open_xcf(template_file)
    image = create_from_template_image(template)
    return image


def create_from_file(file):
    """
    :type file: str
    :return: gimp.Image
    """
    image = gimp.pdb.gimp_file_load(file, file)
    return image
