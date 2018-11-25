import os

import numpy as np

from pgimp.GimpFile import GimpFile
from pgimp.util import file
from pgimp.util.TempFile import TempFile

if __name__ == '__main__':
    img_path = file.relative_to(__file__, '../../../doc/source/_static/img')
    png_file = os.path.join(img_path, 'sphere.png')

    # generate sphere data
    x = np.arange(-1, 1, 0.01)
    y = np.arange(-1, 1, 0.01)
    xx, yy = np.meshgrid(x, y, sparse=True)
    z = np.sin(xx**2 + yy**2)

    # generate rgb image data
    img = np.zeros(shape=(200, 200, 3), dtype=np.uint8)
    img[:, :, 0] = (1-z)*255

    # create temporary gimp file an export to png
    with TempFile('.xcf') as tmp:
        GimpFile(tmp).create('Background', img).export(png_file)
