import io
import os
import tempfile
import textwrap
from enum import Enum
from typing import List, Union

import numpy as np

from pgimp.GimpException import GimpException
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.layers.Layer import Layer


class GimpFileType(Enum):
    RGB = 0
    GRAY = 1


class LayerType(Enum):
    INDEXED = 4


class ColorMap(Enum):
    JET = 'COLORMAP_JET'


image_type_to_layer_type = {
    GimpFileType.RGB: 0,
    GimpFileType.GRAY: 2,
}


class DataFormatException(GimpException):
    pass


class GimpFile:
    def __init__(self, file: str) -> None:
        super().__init__()
        self._file = file
        self._gsr = GimpScriptRunner()
        self._layer_conversion_timeout_in_seconds = 10
        self._short_running_timeout_in_seconds = 5

    def create(self, layer_name: str, layer_content: np.ndarray):
        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_content)

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            import numpy as np
            from pgimp.gimp.file import save_xcf
            
            image = gimp.pdb.gimp_image_new({0:d}, {1:d}, {2:d})
            layer = gimp.pdb.gimp_layer_new(image, image.width, image.height, {4:d}, '{5:s}', 100, gimpenums.NORMAL_MODE)
            array = np.load('{6:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            
            gimp.pdb.gimp_image_add_layer(image, layer, 0)
            save_xcf(image, '{3:s}')
            """
        ).format(width, height, image_type.value, self._file, layer_type, layer_name, tmpfile)

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)

    def create_indexed(self, layer_name: str, layer_content: np.ndarray, colormap: Union[np.ndarray, ColorMap]):
        if isinstance(colormap, np.ndarray):
            if not len(layer_content.shape) == 2 and not (len(layer_content.shape) == 3 and layer_content.shape[2] == 1):
                raise DataFormatException('Indexed images can only contain one channel')
            colormap = 'np.frombuffer({0}, dtype=np.uint8).reshape((256, 3))'.format(colormap.tobytes())
        if isinstance(colormap, ColorMap):
            colormap = colormap.value

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import numpy as np
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf
            from pgimp.gimp.colormap import *
        
            cmap = {0:s}
            image = gimp.pdb.gimp_image_new({1:d}, {2:d}, gimpenums.GRAY)
            palette_name = gimp.pdb.gimp_palette_new('colormap')
            for i in range(0, cmap.shape[0]):
                gimp.pdb.gimp_palette_add_entry(palette_name, str(i), (int(cmap[i][0]), int(cmap[i][1]), int(cmap[i][2])))
            gimp.pdb.gimp_convert_indexed(image, gimpenums.NO_DITHER, gimpenums.CUSTOM_PALETTE, 256, False, False, palette_name)
            
            layer = gimp.pdb.gimp_layer_new(image, image.width, image.height, gimpenums.INDEXED_IMAGE, '{4:s}', 100, gimpenums.NORMAL_MODE)
            array = np.load('{5:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            gimp.pdb.gimp_image_add_layer(image, layer, 0)
        
            save_xcf(image, '{3:s}')
            """
        ).format(colormap, layer_content.shape[1], layer_content.shape[0], self._file, layer_name, tmpfile)

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)

    def layer_to_numpy(self, layer_name: str) -> np.ndarray:
        bytes = self._gsr.execute_binary(textwrap.dedent(
            """
            import gimp
            import numpy as np
            import sys
            from pgimp.gimp.file import open_xcf

            image = open_xcf('{0:s}')
            layer_name = '{1:s}'
            layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
            region = layer.get_pixel_rgn(0, 0, layer.width,layer.height)
            buffer = region[:, :]
            bpp = region.bpp
            np_buffer = np.frombuffer(buffer, dtype=np.uint8).reshape((layer.height, layer.width, bpp))

            np.save(sys.stdout, np_buffer)
            """
        ).format(self._file, layer_name), timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        return np.load(io.BytesIO(bytes))

    def numpy_to_layer(self, layer_name: str, layer_content: np.ndarray, opacity: float=100.0, visible: bool=True, position: int=0, type: LayerType=None):
        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_content)
        if type is not None:
            layer_type = type.value

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            import numpy as np
            from pgimp.gimp.file import open_xcf, save_xcf

            image = open_xcf('{2:s}')
            layer = gimp.pdb.gimp_layer_new(image, {0:d}, {1:d}, {3:d}, '{4:s}', 100, gimpenums.NORMAL_MODE)
            layer.visible = {6:s}
            layer.opacity = float({7:s})
            array = np.load('{5:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes

            gimp.pdb.gimp_image_add_layer(image, layer, {8:d})
            save_xcf(image, '{2:s}')
            """
        ).format(width, height, self._file, layer_type, layer_name, tmpfile, str(visible), str(opacity), position)

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)

    def _numpy_array_info(self, content: np.ndarray):
        if len(content.shape) == 2:
            height, width = content.shape
            depth = 1
        elif len(content.shape) == 3 and content.shape[2] in [1, 3]:
            height, width, depth = content.shape
        else:
            raise DataFormatException('Unrecognized input data shape: ' + repr(content.shape))

        if depth == 1:
            image_type = GimpFileType.GRAY
        elif depth == 3:
            image_type = GimpFileType.RGB
        else:
            raise DataFormatException('Wrong image depth {:d}'.format(depth))

        layer_type = image_type_to_layer_type[image_type]

        return height, width, depth, image_type, layer_type

    def add_layer_from(self, other_file: 'GimpFile', name: str, new_name: str=None, new_type: GimpFileType=GimpFileType.RGB, new_position: int=0):
        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf
            
            image_dst = open_xcf('{0:s}')
            image_src = open_xcf('{1:s}')
            layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, '{3:s}')
            layer_dst = gimp.pdb.gimp_layer_new(image_dst, layer_src.width, layer_src.height, {4:d}, '{2:s}', 100, gimpenums.NORMAL_MODE)
            gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, {5:d})
            gimp.pdb.gimp_edit_copy(layer_src)
            layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
            gimp.pdb.gimp_floating_sel_anchor(layer_floating)
            save_xcf(image_dst, '{0:s}')
            """
        ).format(self._file, other_file._file, new_name or name, name, new_type.value, new_position)

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

    def merge_layer_from(self, other_file: 'GimpFile', name: str):
        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf

            image_dst = open_xcf('{0:s}')
            image_src = open_xcf('{1:s}')
            layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, '{2:s}')
            layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, '{2:s}')
            gimp.pdb.gimp_edit_copy(layer_src)
            layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
            gimp.pdb.gimp_floating_sel_anchor(layer_floating)
            save_xcf(image_dst, '{0:s}')
            """
        ).format(self._file, other_file._file, name)

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

    def layers(self) -> List[Layer]:
        """
        Returns the image layers. The topmost layer is the first element, the bottommost the last element.
        :return:
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf, save_xcf
            
            image = open_xcf('{0:s}')
            
            result = []
            for layer in image.layers:
                properties = dict()
                properties['name'] = layer.name
                properties['visible'] = layer.visible
                properties['opacity'] = layer.opacity
                result.append(properties)
            
            return_json(result)
            """.format(self._file)
        )

        result = self._gsr.execute_and_parse_json(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        layers = []
        for idx, layer_properties in enumerate(result):
            layer_properties['position'] = idx
            layers.append(Layer(layer_properties))

        return layers
