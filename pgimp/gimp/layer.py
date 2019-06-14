# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import List

import numpy as np

import gimp
import gimpenums


class LayerException(Exception):
    pass


class LayerExistsException(LayerException):
    pass


class LayerDoesNotExistException(LayerException):
    pass


def copy_or_merge_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst=0, clear_selection=True):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type position_dst: int
    :type merge: bool
    :type clear_selection: bool 
    :rtype: gimp.Layer
    """
    if clear_selection:
        gimp.pdb.gimp_selection_none(image_src)
    
    layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, layer_name_src)
    if layer_src is None:
        raise LayerDoesNotExistException('Missing source layer ' + layer_name_src + '.')
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)
    if layer_dst is None:
        layer_dst = gimp.pdb.gimp_layer_new(
            image_dst,
            layer_src.width,
            layer_src.height,
            layer_src.type,
            layer_name_dst,
            layer_src.opacity,
            layer_src.mode
        )
        gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, 0)

    gimp.pdb.gimp_edit_copy(layer_src)
    layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
    gimp.pdb.gimp_floating_sel_anchor(layer_floating)
    reorder_layer(image_dst, layer_dst, position_dst)
    return layer_dst


def copy_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst=0, clear_selection=True):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type position_dst: int
    :type merge: bool
    :type clear_selection: bool
    :rtype: gimp.Layer
    """
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)
    if layer_dst is not None:
        raise LayerExistsException('Destination layer ' + layer_name_dst + ' already exists.')
    return copy_or_merge_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst, clear_selection)


def merge_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst=0, clear_selection=True):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type position_dst: int
    :type merge: bool
    :type clear_selection: bool
    :rtype: gimp.Layer
    """
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)
    if layer_dst is None:
        raise LayerDoesNotExistException('Destination layer ' + layer_name_dst + ' does not exist.')
    return copy_or_merge_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst, clear_selection)


def reorder_layer(image, layer, position):
    """
    :type image: gimp.Image
    :type layer: gimp.Layer
    :type position: int
    """
    gimp.pdb.gimp_image_reorder_item(image, layer, None, position)


def merge_mask_layer(
    image_src, 
    layer_name_src, 
    image_dst, 
    layer_name_dst, 
    mask_foreground_color, 
    position_dst=0, 
    clear_selection=True
):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type mask_foreground_color: int
    :type position_dst: int
    :type clear_selection: bool
    :rtype: gimp.Layer
    """
    if clear_selection:
        gimp.pdb.gimp_selection_none(image_src)

    if mask_foreground_color not in [0, 1]:
        raise ValueError('Mask foreground color must be 1 for white and 0 for black')
    if image_dst.base_type != image_src.base_type:
        raise ValueError('Image types must match')
    if image_src.base_type == gimpenums.RGB:
        bpp = 3
    elif image_src.base_type == gimpenums.GRAY:
        bpp = 1
    else:
        raise ValueError('Image must be rgb or gray')

    layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, layer_name_src)
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)

    if layer_src is None:
        if mask_foreground_color == 1:  # white
            content_src = np.zeros(shape=(image_dst.height, image_dst.width))
        else:  # black
            content_src = np.ones(shape=(image_dst.height, image_dst.width))*255
    else:
        region = layer_src.get_pixel_rgn(0, 0, layer_src.width, layer_src.height)
        buffer = region[:, :]
        content_src = np.frombuffer(buffer, dtype=np.uint8).reshape((layer_src.height, layer_src.width, bpp))

    if layer_dst is None:
        if mask_foreground_color == 1:  # white
            content_dst = np.zeros(shape=(image_dst.height, image_dst.width))
        else:  # black
            content_dst = np.ones(shape=(image_dst.height, image_dst.width))*255
    else:
        region = layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
        buffer = region[:, :]
        content_dst = np.frombuffer(buffer, dtype=np.uint8).reshape((layer_dst.height, layer_dst.width, bpp))

    if mask_foreground_color == 1:  # white
        content_merged = np.maximum(content_src, content_dst).astype(np.uint8)
    else:  # black
        content_merged = np.minimum(content_src, content_dst).astype(np.uint8)

    if layer_dst is None:
        if image_src.base_type == gimpenums.RGB:  # rgb
            layer_type = gimpenums.RGB_IMAGE
        else:  # gray
            layer_type = gimpenums.GRAY_IMAGE

        layer_dst = gimp.pdb.gimp_layer_new(
            image_dst,
            content_merged.shape[1],
            content_merged.shape[0],
            layer_type,
            layer_name_dst,
            100,
            gimpenums.NORMAL_MODE
        )
        gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, 0)

    layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)[:, :] = content_merged.tobytes()
    reorder_layer(image_dst, layer_dst, position_dst)
    return layer_dst


def remove_layer(image, layer_name):
    """
    :type image: gimp.Image
    :type layer_name: str
    """
    layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
    gimp.pdb.gimp_image_remove_layer(image, layer)


def add_layer_from_numpy(image, numpy_file, name, width, height, type, position=0, opacity=100., mode=gimpenums.NORMAL_MODE, visible=True):
    """
    :type image: gimp.Image
    :type numpy_file: str
    :type name: strImage
    :type width: int
    :type height: int
    :type type: int
    :type position: int
    :type opacity: float
    :type mode: int
    :type visible: bool
    :rtype: gimp.Layer
    """
    layer = gimp.pdb.gimp_layer_new(image, width, height, type, name, opacity, mode)
    layer.visible = visible
    array = np.load(numpy_file)
    bytes = np.uint8(array).tobytes()
    region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
    region[:, :] = bytes

    gimp.pdb.gimp_image_add_layer(image, layer, position)
    return layer


def add_layer_from_file(image, image_file, name, position=0, opacity=100., mode=gimpenums.NORMAL_MODE, visible=True):
    """"
    :type image: gimp.Image
    :type image_file: str
    :type name: str
    :type position: int
    :type opacity: float
    :type mode: int
    :type visible: bool
    :rtype: gimp.Layer
    """
    image_from_file = gimp.pdb.gimp_file_load(image_file, image_file)

    layer = copy_layer(image_from_file, image_from_file.layers[0].name, image, name, position)
    layer.opacity = opacity
    layer.mode = mode
    layer.visible = visible

    return gimp.pdb.gimp_image_add_layer(image, layer, position)


def convert_layer_to_numpy(image, layer_name):
    """
    :type image: gimp.Image
    :param layer_name: str
    :rtype: np.ndarray
    """
    layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
    region = layer.get_pixel_rgn(0, 0, layer.width, layer.height)
    buffer = region[:, :]
    bpp = region.bpp
    np_buffer = np.frombuffer(buffer, dtype=np.uint8).reshape((layer.height, layer.width, bpp))
    return np_buffer


def convert_layers_to_numpy(image, layer_names):
    """
    :type image: gimp.Image
    :type layer_names: List[str]
    :rtype: np.ndarray
    """
    layer_list = []
    for layer_name in layer_names:
        layer_list.append(convert_layer_to_numpy(image, layer_name))
    return np.concatenate(layer_list, axis=2)
