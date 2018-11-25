import os

import numpy as np

from pgimp.GimpFile import GimpFile
from pgimp.util import file

if __name__ == '__main__':
    img_path = file.relative_to(__file__, '../../../doc/source/_static/img')
    gimp_file = GimpFile(os.path.join(img_path, 'generated_file.xcf'))

    x = np.arange(-1, 1, 0.01)
    y = np.arange(-1, 1, 0.01)
    xx, yy = np.meshgrid(x, y, sparse=True)
    z = np.sin(xx**2 + yy**2)

    img = np.zeros(shape=(200, 200, 3))
    img[:, :, 0] = 1-z

    gimp_file.create('Background', img)
