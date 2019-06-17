# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import tempfile

import numpy as np
from pytest import approx

from pgimp.GimpFile import GimpFile, LayerType, ColorMap, GimpFileType
from pgimp.util import file
from pgimp.util.TempFile import TempFile

rgb_file = GimpFile(file.relative_to(__file__, 'test-resources/rgb.xcf'))
"""
The file rgb.xcf contains a 3x2 image with white 'Background' layer and 'Red', 'Green', 'Blue' layers with differing 
opacity. The layer 'Background' contains a black pixel at y=0, x=1, the others pixels are white.
"""


def test_layer_to_numpy():
    actual = rgb_file.layer_to_numpy('Background')
    expected = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    assert np.all(expected == actual)
    assert actual.shape == (2, 3, 3)


def test_layers_to_numpy():
    with TempFile('.xcf') as f:
        gimp_file = GimpFile(f) \
            .create('Red', np.zeros(shape=(1, 2, 3), dtype=np.uint8)) \
            .add_layer_from_numpy('Green', np.ones(shape=(1, 2, 3), dtype=np.uint8) * 127) \
            .add_layer_from_numpy('Blue', np.ones(shape=(1, 2, 3), dtype=np.uint8) * 255)
        np_array = gimp_file.layers_to_numpy(['Red', 'Green', 'Blue'])

    assert (1, 2, 9) == np_array.shape
    assert np.all(np.array([
        [[0, 0, 0, 127, 127, 127, 255, 255, 255], [0, 0, 0, 127, 127, 127, 255, 255, 255]],
    ], dtype=np.uint8) == np_array)


def test_create():
    filename = file.relative_to(__file__, 'test-resources/test-create.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(filename)
    gimp_file.create('Background', layer_bg)

    exists = os.path.exists(filename)
    actual = gimp_file.layer_to_numpy('Background')
    os.remove(filename)

    assert exists
    assert np.all(layer_bg == actual)


def test_add_layer_from_numpy():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)
    layer_fg = np.array([
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(tmp_file)
    gimp_file.create('Background', layer_bg)
    gimp_file.add_layer_from_numpy('Foreground', layer_fg, opacity=55., visible=False)

    actual_bg = gimp_file.layer_to_numpy('Background')
    actual_fg = gimp_file.layer_to_numpy('Foreground')

    os.remove(tmp_file)

    assert np.all(layer_bg == actual_bg)
    assert np.all(layer_fg == actual_fg)


def test_add_layer_from_numpy_with_position_index():
    data = np.array([[[255, 255, 255]]], dtype=np.uint8)
    with TempFile('.xcf') as tmp_file:
        gimp_file = GimpFile(tmp_file)
        gimp_file.create('Background', data)
        gimp_file.add_layer_from_numpy('Layer 1', data, position=1)
        gimp_file.add_layer_from_numpy('Layer 2', data, position=1)

        assert gimp_file.layer_names() == ['Background', 'Layer 2', 'Layer 1']


def test_add_layer_from_numpy_with_position_layer_name():
    data = np.array([[[255, 255, 255]]], dtype=np.uint8)
    with TempFile('.xcf') as tmp_file:
        gimp_file = GimpFile(tmp_file)
        gimp_file.create('Background', data)
        gimp_file.add_layer_from_numpy('Layer 1', data, position='Background')
        gimp_file.add_layer_from_numpy('Layer 2', data, position='Background')

        assert gimp_file.layer_names() == ['Layer 1', 'Layer 2', 'Background']


def test_add_layer_from_file():
    with TempFile('.xcf') as dst, TempFile('.xcf') as src:
        layer_bg = np.array([
            [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
        ], dtype=np.uint8)
        position = 1

        src_file = GimpFile(src)
        src_file.create('Background', np.zeros(shape=(2, 3, 3), dtype=np.uint8))
        src_file.add_layer_from_numpy('Yellow', np.array([
            [[240, 255, 0], [240, 255, 0], [240, 255, 0]],
            [[240, 255, 0], [240, 255, 0], [240, 255, 0]],
        ], dtype=np.uint8))

        dst_file = GimpFile(dst)
        dst_file.create('Background', layer_bg)
        dst_file.add_layer_from_file(src_file, 'Yellow', new_name='Yellow (copied)', new_position=position)

        assert 'Yellow (copied)' == dst_file.layers()[position].name
        assert np.all([240, 255, 0] == dst_file.layer_to_numpy('Yellow (copied)'))


def test_merge_layer_from_file():
    with TempFile('.xcf') as dst, TempFile('.xcf') as src:
        layer_bg = np.array([
            [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
        ], dtype=np.uint8)

        src_file = GimpFile(src)
        src_file.create('Background', np.zeros(shape=(2, 3, 3), dtype=np.uint8))
        src_file.add_layer_from_numpy('Yellow', np.array([
            [[240, 255, 0], [240, 255, 0], [240, 255, 0]],
            [[240, 255, 0], [240, 255, 0], [240, 255, 0]],
        ], dtype=np.uint8))

        dst_file = GimpFile(dst)
        dst_file.create('Yellow', layer_bg)
        dst_file.merge_layer_from_file(src_file, 'Yellow')

        new_layer_contents = dst_file.layer_to_numpy('Yellow')

        assert np.all([240, 255, 0] == new_layer_contents)


def test_merge_layer_from_file_with_cleared_selection():
    src = file.relative_to(__file__, 'test-resources/selection.xcf')
    with TempFile('.xcf') as dst:
        src_file = GimpFile(src)
        dst_file = GimpFile(dst)
        dst_file.create('Background', np.zeros(shape=(3, 3, 3), dtype=np.uint8))
        dst_file.merge_layer_from_file(src_file, 'Background')

        new_layer_contents = dst_file.layer_to_numpy('Background')

        assert np.all(np.array([
            [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
            [[255, 0, 0], [255, 0, 0], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
        ], dtype=np.uint8) == new_layer_contents)


def test_merge_layer_from_file_without_cleared_selection():
    src = file.relative_to(__file__, 'test-resources/selection.xcf')
    with TempFile('.xcf') as dst:
        src_file = GimpFile(src)
        dst_file = GimpFile(dst)
        dst_file.create('Background', np.zeros(shape=(3, 3, 3), dtype=np.uint8))
        dst_file.merge_layer_from_file(src_file, 'Background', clear_selection=False)

        new_layer_contents = dst_file.layer_to_numpy('Background')

        assert np.all(np.array([
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            [[255, 0, 0], [255, 0, 0], [0, 0, 0]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        ], dtype=np.uint8) == new_layer_contents)


def test_layers():
    layers = rgb_file.layers()

    assert ['Blue', 'Green', 'Red', 'Background'] == list(map(lambda x: x.name, layers))
    assert [0, 1, 2, 3] == list(map(lambda x: x.position, layers))
    assert [False, False, False, True] == list(map(lambda x: x.visible, layers))
    assert [23.92156862745098, 40.3921568627451, 52.54901960784314, 100.0] == list(map(lambda x: approx(x.opacity), layers))


def test_convert_to_indexed_using_predefined_colormap():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    values = np.array([[i for i in range(0, 256)]], dtype=np.uint8)
    assert (1, 256) == values.shape

    gimp_file = GimpFile(tmp_file)
    gimp_file.create_indexed('Background', values, ColorMap.JET)
    gimp_file.add_layer_from_numpy('Values', values, type=LayerType.INDEXED)

    layer_bg = gimp_file.layer_to_numpy('Background')
    layer_values = gimp_file.layer_to_numpy('Values')

    os.remove(tmp_file)

    assert (1, 256, 1) == layer_bg.shape
    assert np.all(values == layer_bg[:, :, 0])
    assert (1, 256, 1) == layer_values.shape
    assert np.all(values == layer_values[:, :, 0])


def test_convert_to_indexed_using_custom_colormap():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    values = np.array([[i for i in range(0, 256)]], dtype=np.uint8)
    assert (1, 256) == values.shape
    colormap = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255], *[[i, i, i] for i in range(3, 256)]], dtype=np.uint8)
    assert (256, 3) == colormap.shape

    gimp_file = GimpFile(tmp_file)
    gimp_file.create_indexed('Background', values, colormap=colormap)
    gimp_file.add_layer_from_numpy('Values', values, type=LayerType.INDEXED)

    layer_bg = gimp_file.layer_to_numpy('Background')
    layer_values = gimp_file.layer_to_numpy('Values')

    os.remove(tmp_file)

    assert (1, 256, 1) == layer_bg.shape
    assert np.all(values == layer_bg[:, :, 0])
    assert (1, 256, 1) == layer_values.shape
    assert np.all(values == layer_values[:, :, 0])


def test_remove_layer():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    layer = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(tmp_file)
    gimp_file.create('Background', layer)
    gimp_file.add_layer_from_numpy('Layer', layer)
    all_layers = gimp_file.layer_names()

    gimp_file.remove_layer('Background')
    remaining_layers1 = gimp_file.layer_names()
    gimp_file.remove_layer('Layer')
    remaining_layers2 = gimp_file.layer_names()

    os.remove(tmp_file)

    assert ['Layer', 'Background'] == all_layers
    assert ['Layer'] == remaining_layers1
    assert [] == remaining_layers2


def test_copy():
    with TempFile('.xcf') as original, TempFile('.xcf') as copy:
        original_file = GimpFile(original).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        copied_file = original_file.copy(copy)
        original_file.add_layer_from_numpy('New', np.zeros(shape=(2, 2), dtype=np.uint8))
        assert ['Background'] == copied_file.layer_names()
        assert ['New', 'Background'] == original_file.layer_names()


def test_dimensions():
    assert (3, 2) == rgb_file.dimensions()


def test_create_from_template():
    with TempFile('.xcf') as original, TempFile('.xcf') as created:
        original_file = GimpFile(original).create('Background', np.zeros(shape=(3, 2), dtype=np.uint8))
        created_file = GimpFile(created).create_from_template(original_file)
        assert [] == created_file.layer_names()
        assert (2, 3) == created_file.dimensions()


def test_create_empty():
    with TempFile('.xcf') as f:
        gimp_file = GimpFile(f).create_empty(3, 2, GimpFileType.RGB)
        assert (3, 2) == gimp_file.dimensions()
        assert [] == gimp_file.layer_names()


def test_create_from_file():
    test_export()


def test_export():
    with TempFile('.xcf') as xcf, TempFile('.png') as png,  TempFile('.jpg') as jpg, TempFile('.xcf') as from_png:
        gimp_file = GimpFile(xcf) \
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \
            .add_layer_from_numpy('Foreground', np.ones(shape=(1, 1), dtype=np.uint8) * 255, opacity=50.) \

        gimp_file.export(png)  # saved as grayscale with alpha (identify -format '%[channels]' FILE)
        gimp_file.export(jpg)

        assert np.all([127, 255] == GimpFile(from_png).create_from_file(png, layer_name='Image').layer_to_numpy('Image'))
        assert np.all([127] == GimpFile(from_png).create_from_file(jpg, layer_name='Image').layer_to_numpy('Image'))
