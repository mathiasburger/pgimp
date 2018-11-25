import os

import numpy as np

from pgimp.GimpFile import GimpFile
from pgimp.util import file
from pgimp.util.TempFile import TempFile

if __name__ == '__main__':
    img_path = file.relative_to(__file__, '../../../doc/source/_static/img')
    png_file = os.path.join(img_path, 'mask_applied.png')

    height = 100
    width = 200

    # layer content
    bg = np.zeros(shape=(height, width), dtype=np.uint8)
    fg = np.ones(shape=(height, width), dtype=np.uint8) * 255
    mask = np.zeros(shape=(height, width), dtype=np.uint8)
    mask[:, width//4:3*width//4+1] = 255

    with TempFile('.xcf') as xcf, TempFile('.npz') as npz:
        # create gimp file
        gimp_file = GimpFile(xcf) \
            .create('Background', bg) \
            .add_layer_from_numpy('Foreground', fg) \
            .add_layer_from_numpy('Mask', mask)

        # save layer data to numpy arrays
        arr_bg = gimp_file.layer_to_numpy('Background')
        arr_fg = gimp_file.layer_to_numpy('Foreground')
        arr_mask = gimp_file.layer_to_numpy('Mask')

        # save data as npz
        np.savez_compressed(npz, bg=arr_bg, fg=arr_fg, mask=arr_mask)

        # load data from npz
        loaded = np.load(npz)
        loaded_bg = loaded['bg']
        loaded_fg = loaded['fg']
        loaded_mask = loaded['mask']

    # merge background and foreground using mask
    mask_idxs = loaded_mask == 255
    img = loaded_bg.copy()
    img[mask_idxs] = loaded_fg[mask_idxs]

    with TempFile('.xcf') as xcf:
        # create a temporary gimp file and export to png
        gimp_file = GimpFile(xcf) \
            .create('Background', img) \
            .export(png_file)
