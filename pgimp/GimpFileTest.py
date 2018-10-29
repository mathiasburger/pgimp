import os
import tempfile

import numpy as np

from pgimp.GimpFile import GimpFile
from pgimp.util import file


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


def test_numpy_to_layer():
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
    gimp_file.numpy_to_layer('Foreground', layer_fg, opacity=55., visible=False)

    actual_bg = gimp_file.layer_to_numpy('Background')
    actual_fg = gimp_file.layer_to_numpy('Foreground')

    os.remove(tmp_file)

    assert np.all(layer_bg == actual_bg)
    assert np.all(layer_fg == actual_fg)
